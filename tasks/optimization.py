# from crewai import Task
# from tools.vector_db import VectorDB
# import statistics

# def create_optimization_task(agent, product_name: str):
#     return Task(
#         description=f"""
#         Analyze the collected pricing data for {product_name} and generate optimal pricing strategies.
        
#         Instructions:
#         1. Retrieve pricing data from the vector database
#         2. Analyze competitor pricing patterns
#         3. Consider market positioning (premium, mid-range, budget)
#         4. Calculate optimal price points for maximum profit and customer attraction
#         5. Provide different pricing strategies with reasoning
#         6. Include confidence scores for each strategy
        
#         Focus on electronic device market dynamics and consumer behavior.
#         """,
#         agent=agent,
#         expected_output="Detailed pricing strategy with recommendations, reasoning, and confidence scores"
#     )

# def execute_optimization_task(product_name: str):
#     """Execute price optimization task"""
#     vector_db = VectorDB()
#     pricing_data = vector_db.query_pricing_data(product_name)
    
#     if not pricing_data:
#         return {"error": "No pricing data available for optimization"}
    
#     prices = [float(item['price']) for item in pricing_data]
    
#     # Calculate statistics
#     avg_price = statistics.mean(prices)
#     median_price = statistics.median(prices)
#     min_price = min(prices)
#     max_price = max(prices)
    
#     # Generate pricing strategies
#     strategies = {
#         "competitive": {
#             "price": avg_price * 0.95,  # 5% below average
#             "reasoning": "Slightly undercut competitors to attract price-sensitive customers",
#             "confidence": 0.8,
#             "profit_margin": "15-20%"
#         },
#         "premium": {
#             "price": max_price * 0.9,  # 10% below highest price
#             "reasoning": "Position as premium option with better service/warranty",
#             "confidence": 0.7,
#             "profit_margin": "25-30%"
#         },
#         "penetration": {
#             "price": min_price * 0.95,  # 5% below lowest price
#             "reasoning": "Aggressive pricing to gain market share quickly",
#             "confidence": 0.6,
#             "profit_margin": "5-10%"
#         }
#     }
    
#     # Select recommended strategy based on market analysis
#     recommended_strategy = "competitive"  # Default recommendation
    
#     return {
#         "product_name": product_name,
#         "market_analysis": {
#             "average_competitor_price": avg_price,
#             "price_range": {"min": min_price, "max": max_price},
#             "total_competitors": len(pricing_data)
#         },
#         "recommended_strategy": recommended_strategy,
#         "strategies": strategies,
#         "recommendation_reasoning": "Competitive pricing balances market penetration with profitability"
#     }