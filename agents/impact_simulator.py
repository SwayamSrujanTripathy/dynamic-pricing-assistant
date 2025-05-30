from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.agents import create_react_agent, AgentExecutor
from config.settings import LLAMA_MODEL_NAME
import logging
import re
 
logger = logging.getLogger(__name__)
 
class ImpactSimulatorAgent:
    def __init__(self):
        self.llm = Ollama(model=LLAMA_MODEL_NAME)
        self.tools = []
        self.last_simulation = None
 
        template = """
        You are an impact simulator. Estimate customer influx and profit margins for a pricing strategy. No tools available; use reasoning.
 
        Available tools: {tools}
        Tool names: {tool_names}
 
        Respond in:
        ```
        Thought: <Reasoning>
        Action: simulation_result
        Action Input: <Customer influx and margin estimate>
        ```
 
        Agent scratchpad: {agent_scratchpad}
 
        Base estimates on price provided in query.
 
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
 
    def run(self, query: str, suggested_price: str = None) -> dict:
        try:
            # Extract price from suggested_price or query
            price = 0
            if suggested_price:
                price_str = suggested_price.replace("₹", "").replace(",", "")
                price = float(price_str) if price_str else 0
            else:
                match = re.search(r'₹([\d,]+)', query)
                if match:
                    price = float(match.group(1).replace(",", ""))
 
            result = self.executor.invoke({"input": query})
            output = result.get("output", "")
 
            if "simulation_result" in output.lower():
                self.last_simulation = output.split("Action Input:")[-1].strip()
                return {"impact": self.last_simulation}
 
            # Estimate based on price
            if price > 50000:
                influx = "8% customer influx"
                margin = "20% profit margin"
            elif price > 20000:
                influx = "12% customer influx"
                margin = "15% profit margin"
            else:
                influx = "15% customer influx"
                margin = "10% profit margin"
 
            impact = f"{influx} with {margin} for {suggested_price or 'unknown price'}"
            self.last_simulation = impact
            return {"impact": impact}
 
        except Exception as e:
            logger.error(f"ImpactSimulatorAgent error: {e}")
            if self.last_simulation:
                return {"impact": self.last_simulation}
            return {"impact": f"Error: {str(e)}; estimated 12% influx with 15% margin"}