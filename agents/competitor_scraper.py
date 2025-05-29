from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from tools.web_scraper import web_scraper
from tools.vector_db_tools import store_in_pinecone, query_pinecone
from config.settings import LLAMA_MODEL_NAME
import uuid

class CompetitorScraperAgent:
    def __init__(self):
        self.llm = Ollama(model=LLAMA_MODEL_NAME)
        self.prompt = PromptTemplate(
            input_variables=["input", "tools", "tool_names", "agent_scratchpad"],
            template="""You are a competitor scraper agent. Your task is to scrape Flipkart for products matching the user-provided name and specifications, extract pricing data, and store it in Pinecone. Use the provided tools to scrape and store data.

            Tools available: {tool_names}

            Tool descriptions: {tools}

            User input: {input}

            Agent scratchpad: {agent_scratchpad}

            Follow these steps:
            1. Use the web_scraper tool to get pricing data for the query.
            2. Store the scraped data in Pinecone using store_in_pinecone.
            3. Return the scraped pricing data in a clear format.

            Respond in the following format:
            ```
            Thought: <Your reasoning about the next step>
            Action: <Tool name, e.g., web_scraper, store_in_pinecone, or Final Answer>
            Action Input: <Input for the tool or final answer text>
            ```

            Example 1 (scraping):
            ```
            Thought: I need to scrape Flipkart for products matching the query.
            Action: web_scraper
            Action Input: Smartphone 8GB RAM 128GB storage 5G
            ```

            Example 2 (storing):
            ```
            Thought: I have the scraped data and need to store it in Pinecone.
            Action: store_in_pinecone
            Action Input: Product: Example Smartphone, Price: ₹1000
            ```

            Example 3 (final answer):
            ```
            Thought: The data is stored, and I need to return the scraped pricing data.
            Action: Final Answer
            Action Input: Scraped Pricing Data: Product: Example Smartphone, Price: ₹1000
            ```

            Provide only the Thought/Action/Action Input format. Do not include JSON, code snippets, or narrative text outside this format.
            """
        )
        self.tools = [web_scraper, store_in_pinecone]
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

    def run(self, product_name, specifications):
        query = f"Product: {product_name}, Specifications: {specifications}"
        result = self.executor.invoke({"input": query})
        return result["output"]