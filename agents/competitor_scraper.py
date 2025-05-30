from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.agents import create_react_agent, AgentExecutor
from config.settings import LLAMA_MODEL_NAME
from tools.web_scraper import web_scraper
from tools.vector_db_tools import store_in_pinecone, query_pinecone
import logging
 
logger = logging.getLogger(__name__)
 
class CompetitorScraperAgent:
    def __init__(self):
        self.llm = Ollama(model=LLAMA_MODEL_NAME)
        self.tools = [web_scraper, store_in_pinecone, query_pinecone]
        self.partial_results = []
 
        for tool in self.tools:
            if not hasattr(tool, 'name') or not hasattr(tool, 'description'):
                logger.error(f"Tool {tool} missing name or description")
                raise ValueError(f"Invalid tool: {tool}")
 
        template = """
        You are a competitor pricing scraper for Amazon.in. Use tools to scrape prices, store data, and retrieve results. Available tools:
        {tools}
 
        Tool names: {tool_names}
 
        Respond in:
        ```
        Thought: <Reasoning>
        Action: <Tool name or Final Answer>
        Action Input: <Input or result>
        ```
 
        Agent scratchpad: {agent_scratchpad}
 
        If no products found, return empty list. Store first product for partial output.
 
        Query: {input}
        """
        self.prompt = PromptTemplate(
            input_variables=["input", "agent_scratchpad", "tool_names", "tools"],
            template=template
        )
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10
        )
 
    def run(self, query: str) -> dict:
        try:
            result = self.executor.invoke({"input": query})
            output = result.get("output", "")
 
            if isinstance(output, dict) and "products" in output:
                products = output["products"]
                if products:
                    self.partial_results.extend(products)
                    for product in products:
                        store_in_pinecone.invoke(product)
                return {"products": products}
            elif "products" in output.lower():
                try:
                    products = eval(output).get("products", []) if "{" in output else []
                    if products:
                        self.partial_results.extend(products)
                        for product in products:
                            store_in_pinecone.invoke(product)
                    return {"products": products}
                except:
                    pass
 
            if self.partial_results:
                return {"products": [self.partial_results[0]]}
 
            return {"products": []}
 
        except Exception as e:
            logger.error(f"CompetitorScraperAgent error: {e}")
            if self.partial_results:
                return {"products": [self.partial_results[0]]}
            return {"products": [], "error": str(e)}