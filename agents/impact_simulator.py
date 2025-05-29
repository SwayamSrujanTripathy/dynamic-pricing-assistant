from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from config.settings import LLAMA_MODEL_NAME

class ImpactSimulatorAgent:
    def __init__(self):
        self.llm = Ollama(model=LLAMA_MODEL_NAME)
        self.prompt = PromptTemplate(
            input_variables=["input", "tools", "tool_names", "agent_scratchpad"],
            template="""You are an impact simulator agent. Your task is to simulate the impact of a suggested pricing strategy on customer influx and profit margins.

            Tools available: {tool_names}

            Tool descriptions: {tools}

            User input: {input}

            Agent scratchpad: {agent_scratchpad}

            Follow these steps:
            1. Interpret the suggested price and strategy from the input.
            2. Simulate the impact (e.g., estimate increased customer influx or profit margins).
            3. Return the simulated impact.

            Respond in the following format:
            ```
            Thought: <Your reasoning about the next step>
            Action: Final Answer
            Action Input: <Simulated impact text>
            ```

            Example:
            ```
            Thought: I need to simulate the impact of the pricing strategy.
            Action: Final Answer
            Action Input: Pricing at ₹29,000 may increase customer influx by 10% and maintain a 12% profit margin.
            ```

            Provide only the Thought/Action/Action Input format. Do not include JSON, code snippets, or narrative text outside this format.
            """
        )
        self.tools = []
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

    def run(self, pricing_strategy):
        result = self.executor.invoke({"input": pricing_strategy})
        return result["output"]