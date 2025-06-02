import time
import logging
import json
import os
import warnings
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.agents import create_react_agent, AgentExecutor
from config.settings import LLAMA_MODEL_NAME
from tools.web_scraper import web_scraper
from tools.vector_db_tools import store_in_pinecone
from pydantic import BaseModel
 
# Suppress huggingface_hub FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning, module="huggingface_hub")
 
logger = logging.getLogger(__name__)
 
class CompetitorScraperAgent:
    def __init__(self):
        self.llm = OllamaLLM(model=LLAMA_MODEL_NAME)
        self.tools = [web_scraper, store_in_pinecone]
        self.partial_results = []
 
        for tool in self.tools:
            if not hasattr(tool, 'name') or not hasattr(tool, 'description'):
                logger.error(f"Invalid tool: {tool}")
                raise ValueError(f"Tool {tool} missing name or description")
 
        template = """
        You are a competitor pricing scraper for Amazon.in and Flipkart.com. Scrape the top product price matching the product name and specifications. If no products are found, try simplified queries (e.g., append "5G", remove specifications, try product name only) and switch platforms.
 
        Available tools: {tool_names}
        Tools details: {tools}
 
        Respond with:
        - Thought: Your reasoning process
        - Action: invoke_tool
        - Action Input: JSON object with tool name and input query
 
        Agent scratchpad: {agent_scratchpad}
        Input: {query}
        """
        self.prompt = PromptTemplate(
            input_variables=["query", "agent_scratchpad", "tools", "tool_names"],
            template=template,
            partial_variables={"tools": [f"{tool.name}: {tool.description}" for tool in self.tools], "tool_names": [tool.name for tool in self.tools]}
        )
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
 
        class ExecutorConfig(BaseModel):
            class Config:
                arbitrary_types_allowed = True
 
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
            model_config=ExecutorConfig.Config
        )
 
    def execute(self, query: str) -> dict:
        try:
            logger.info(f"Executing CompetitorScraperAgent with query: {query}")
            query_variations = [query]
            if "Specifications:" in query:
                product = query.split("Specifications:")[0].replace("Product:", "").strip()
                specs = query.split("Specifications:")[1].strip()
                query_variations.append(f"Product: {product} 5G, Specifications: {specs}")
                query_variations.append(f"Product: {product}")
                query_variations.append(f"Product: {product} 5G")
 
            products = []
            for q in query_variations:
                logger.info(f"Trying query variation: {q}")
                result = self.executor.invoke({
                    "query": q,
                    "tool_names": [tool.name for tool in self.tools],
                    "tools": [f"{tool.name}: {tool.description}" for tool in self.tools],
                    "agent_scratchpad": ""
                })
                logger.info(f"ReAct agent output: {json.dumps(result, indent=2)}")
 
                if isinstance(result.get("output"), list):
                    for output in result["output"]:
                        if isinstance(output, dict) and "products" in output:
                            products.extend(output["products"])
                elif isinstance(result.get("output"), dict) and "products" in result["output"]:
                    products.extend(result["output"]["products"])
 
                if products:
                    break
 
            if products:
                os.makedirs("data/scraped_data", exist_ok=True)
                with open(f"data/scraped_data/scraped_{int(time.time())}.json", "w") as f:
                    json.dump(products, f, indent=2)
                for product in products:
                    self.partial_results.append(product)
                    store_in_pinecone.invoke(product)
                logger.info(f"Scraped {len(products)} products")
                return {"products": products}
 
            logger.warning("No products found from Amazon.in or Flipkart.com")
            return {"products": []}
 
        except Exception as e:
            logger.error(f"CompetitorScraperAgent error: {e}")
            if self.partial_results:
                return {"products": [self.partial_results[0]]}
            return {"products": [], "error": str(e)}