from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.agents import create_react_agent, AgentExecutor
from config.settings import LLAMA_MODEL_NAME
from tools.vector_db_tools import query_pinecone
import logging
import re
 
logger = logging.getLogger(__name__)
 
class PriceOptimizerAgent:
    def __init__(self):
        self.llm = Ollama(model=LLAMA_MODEL_NAME)
        self.tools = [query_pinecone]
        self.partial_price = None
 
        for tool in self.tools:
            if not hasattr(tool, 'name') or not hasattr(tool, 'description'):
                logger.error(f"Tool {tool} missing name or description")
                raise ValueError(f"Invalid tool: {tool}")
 
        template = """
        You are a price optimizer. Use tools to retrieve competitor prices and suggest a pricing strategy. Available tools:
        {tools}
 
        Tool names: {tool_names}
 
        Respond in:
        ```
        Thought: <Reasoning>
        Action: <Tool name or Final Answer>
        Action Input: <Input or result>
        ```
 
        Agent scratchpad: {agent_scratchpad}
 
        If no data, use partial data or default to competitive pricing.
 
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
 
    def run(self, query: str, partial_data: list = None) -> dict:
        try:
            result = self.executor.invoke({"input": query})
            output = result.get("output", "")
 
            # Process partial data if available
            if partial_data and not self.partial_price:
                prices = []
                for item in partial_data:
                    price_str = item.get("price", "₹0").replace("₹", "").replace(",", "")
                    try:
                        prices.append(float(price_str))
                    except ValueError:
                        continue
                if prices:
                    avg_price = sum(prices) / len(prices)
                    suggested_price = avg_price * 0.95  # 5% below
                    return {
                        "suggested_price": f"₹{int(suggested_price):,}",
                        "strategy": "Competitive pricing (5% below average)"
                    }
 
            # Process Pinecone data
            if "products" in output.lower():
                products = eval(output).get("products", []) if "{" in output else []
                prices = []
                for product in products:
                    price_str = product.get("price", "₹0").replace("₹", "").replace(",", "")
                    try:
                        prices.append(float(price_str))
                    except ValueError:
                        continue
                if prices:
                    avg_price = sum(prices) / len(prices)
                    suggested_price = avg_price * 0.95
                    return {
                        "suggested_price": f"₹{int(suggested_price):,}",
                        "strategy": "Competitive pricing (5% below average)"
                    }
 
            return {"suggested_price": "₹0", "strategy": "No data available"}
 
        except Exception as e:
            logger.error(f"PriceOptimizerAgent error: {e}")
            if partial_data:
                prices = []
                for item in partial_data:
                    price_str = item.get("price", "₹0").replace("₹", "").replace(",", "")
                    try:
                        prices.append(float(price_str))
                    except ValueError:
                        continue
                if prices:
                    avg_price = sum(prices) / len(prices)
                    suggested_price = avg_price * 0.95
                    return {
                        "suggested_price": f"₹{int(suggested_price):,}",
                        "strategy": "Competitive pricing (5% below average)"
                    }
            return {"suggested_price": "₹0", "strategy": f"Error: {str(e)}"}