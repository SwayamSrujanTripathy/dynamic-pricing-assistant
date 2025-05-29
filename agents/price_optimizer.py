from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from tools.vector_db_tools import query_pinecone
from config.settings import LLAMA_MODEL_NAME

class PriceOptimizerAgent:
    def __init__(self):
        self.llm = Ollama(model=LLAMA_MODEL_NAME)
        self.prompt = PromptTemplate(
            input_variables=["input", "tools", "tool_names", "agent_scratchpad"],
            template="""You are a price optimizer agent. Your task is to analyze competitor pricing data from Pinecone and suggest a dynamic pricing strategy to maximize customer influx and profit margins.

            Tools available: {tool_names}

            Tool descriptions: {tools}

            User input: {input}

            Agent scratchpad: {agent_scratchpad}

            Follow these steps:
            1. Use query_pinecone to retrieve competitor pricing data.
            2. Analyze the pricing data to suggest an optimal price (e.g., slightly below average competitor price).
            3. Return the suggested price and strategy.

            Respond in the following format:
            ```
            Thought: <Your reasoning about the next step>
            Action: <Tool name, e.g., query_pinecone, or Final Answer>
            Action Input: <Input for the tool or final answer text>
            ```

            Example 1 (querying):
            ```
            Thought: I need to retrieve competitor pricing data from Pinecone.
            Action: query_pinecone
            Action Input: Pricing for Product: Smartphone, Specifications: 8GB RAM, 128GB storage, 5G
            ```

            Example 2 (final answer):
            ```
            Thought: I have analyzed the pricing data and can suggest a strategy.
            Action: Final Answer
            Action Input: Suggested price: ₹29,000. Strategy: Set 5% below average competitor price to increase customer influx.
            ```

            Provide only the Thought/Action/Action Input format. Do not include JSON, code snippets, or narrative text outside this format.
            """
        )
        self.tools = [query_pinecone]
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

    def run(self, product_name, specifications):
        query = f"Analyze pricing for Product: {product_name}, Specifications: {specifications}"
        result = self.executor.invoke({"input": query})
        return result["output"]