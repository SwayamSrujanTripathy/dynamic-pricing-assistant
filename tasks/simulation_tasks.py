# from crewai import Task
# import random

# def create_simulation_task(agent, optimization_result: dict):
#     return Task(
#         description=f"""
#         Simulate the business impact of the recommended pricing strategy.
        
#         Based on the optimization results:
#         - Recommended Strategy: {optimization_result.get('recommended_strategy', 'N/A')}
#         - Market Analysis: {optimization_result.get('market_analysis', {})}
        
#         Instructions:
#         1. Project sales volume impact based on pricing strategy
#         2. Estimate revenue projections
#         3. Assess market share implications
#         4. Evaluate customer satisfaction impact
#         5. Identify potential risks and mitigation strategies
#         6. Provide confidence intervals for projections
        
#         Consider electronic device market characteristics and seasonal factors.
#         """,
#         agent=agent,
#         expected_output="Comprehensive impact analysis with metrics, projections, and risk assessment"
#     )

# def execute_simulation_task(optimization_result: dict):
#     """Execute impact simulation task"""
#     if not optimization_result or "error" in optimization_result:
#         return {"error": "Cannot simulate without valid optimization results"}
    
#     recommended_strategy = optimization_result.get('recommended_strategy', 'competitive')
#     strategies = optimization_result.get('strategies', {})
    
#     if recommended_strategy not in strategies:
#         return {"error": "Invalid strategy for simulation"}
    
#     strategy_data = strategies[recommended_strategy]
#     recommended_price = strategy_data['price']
    
#     # Simulate business impact (simplified model)
#     base_volume = 1000  # Base monthly sales volume
    
#     # Price elasticity simulation
#     market_avg = optimization_result['market_analysis']['average_competitor_price']
#     price_difference_pct = (recommended_price - market_avg) / market_avg
    
#     # Volume impact based on price positioning
#     if recommended_strategy == "penetration":
#         volume_multiplier = 1.3 + random.uniform(-0.1, 0.1)
#         satisfaction_score = 8.5
#     elif recommended_strategy == "premium":
#         volume_multiplier = 0.8 + random.uniform(-0.1, 0.1)
#         satisfaction_score = 7.8
#     else:  # competitive
#         volume_multiplier = 1.1 + random.uniform(-0.05, 0.05)
#         satisfaction_score = 8.2
    
#     projected_volume = int(base_volume * volume_multiplier)
#     projected_revenue = projected_volume * recommended_price
    
#     # Market share estimation (simplified)
#     base_market_share = 5.0  # 5% base market share
#     share_impact = volume_multiplier - 1.0
#     projected_market_share = base_market_share + (share_impact * 2)
    
#     # Risk assessment
#     risks = []
#     if recommended_strategy == "penetration":
#         risks.append("Low profit margins may not be sustainable long-term")
#         risks.append("Competitors may engage in price wars")
#     elif recommended_strategy == "premium":
#         risks.append("Limited market size for premium positioning")
#         risks.append("Higher customer expectations for quality and service")
#     else:
#         risks.append("May not differentiate significantly from competitors")
    
#     return {
#         "product_name": optimization_result.get('product_name', 'Unknown'),
#         "strategy_simulated": recommended_strategy,
#         "recommended_price": recommended_price,
#         "projections": {
#             "monthly_sales_volume": projected_volume,
#             "monthly_revenue": projected_revenue,
#             "market_share_impact": f"{projected_market_share:.1f}%",
#             "customer_satisfaction_score": satisfaction_score
#         },
#         "confidence_intervals": {
#             "volume_range": f"{int(projected_volume * 0.9)}-{int(projected_volume * 1.1)}",
#             "revenue_range": f"${projected_revenue * 0.9:.0f}-${projected_revenue * 1.1:.0f}"
#         },
#         "risk_assessment": risks,
#         "recommendations": [
#             "Monitor competitor responses closely",
#             "Track customer feedback and satisfaction metrics",
#             "Review pricing strategy monthly based on market changes"
#         ]
#     }