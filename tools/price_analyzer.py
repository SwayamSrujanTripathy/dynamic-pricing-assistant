import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import logging
from models.data_models import PricingSource, PricingStrategy, MarketScenario
from config.settings import settings

logger = logging.getLogger(__name__)

class PriceAnalyzerTool:
    def __init__(self):
        self.profit_margin_min = settings.PROFIT_MARGIN_RANGE["min"]
        self.profit_margin_max = settings.PROFIT_MARGIN_RANGE["max"]
        self.competitive_threshold = settings.COMPETITIVE_THRESHOLD
    
    def analyze_competitive_position(self, target_price: float, competitor_prices: List[float]) -> Dict[str, any]:
        """Analyze competitive position of target price"""
        if not competitor_prices:
            return {"position": "unknown", "analysis": "No competitor data available"}
        
        competitor_prices = sorted(competitor_prices)
        min_price = min(competitor_prices)
        max_price = max(competitor_prices)
        avg_price = np.mean(competitor_prices)
        median_price = np.median(competitor_prices)
        
        # Determine position
        if target_price <= min_price:
            position = "lowest"
            percentile = 0
        elif target_price >= max_price:
            position = "highest"
            percentile = 100
        else:
            percentile = (sum(1 for p in competitor_prices if p <= target_price) / len(competitor_prices)) * 100
            if percentile <= 25:
                position = "low"
            elif percentile <= 50:
                position = "below_average"
            elif percentile <= 75:
                position = "above_average"
            else:
                position = "high"
        
        # Calculate competitive gaps
        price_gaps = {
            "to_lowest": target_price - min_price,
            "to_highest": max_price - target_price,
            "to_average": target_price - avg_price,
            "to_median": target_price - median_price
        }
        
        return {
            "position": position,
            "percentile": percentile,
            "price_gaps": price_gaps,
            "market_stats": {
                "min": min_price,
                "max": max_price,
                "average": avg_price,
                "median": median_price,
                "spread": max_price - min_price
            }
        }
    
    def calculate_optimal_price(self, 
                              cost_price: float, 
                              competitor_prices: List[float],
                              strategy: str = "balanced") -> Tuple[float, str]:
        """Calculate optimal price based on strategy"""
        
        if not competitor_prices:
            # No competition data - use cost-plus pricing
            optimal_price = cost_price * (1 + self.profit_margin_min + 0.1)
            rationale = "Cost-plus pricing due to lack of competitive data"
            return optimal_price, rationale
        
        min_competitor = min(competitor_prices)
        max_competitor = max(competitor_prices)
        avg_competitor = np.mean(competitor_prices)
        
        if strategy == "penetration":
            # Price below competition for market entry
            optimal_price = min_competitor * 0.95
            rationale = "Penetration pricing to gain market share"
            
        elif strategy == "premium":
            # Price above competition for premium positioning
            optimal_price = max_competitor * 1.05
            rationale = "Premium pricing for brand positioning"
            
        elif strategy == "competitive":
            # Price at market average
            optimal_price = avg_competitor
            rationale = "Competitive pricing at market average"
            
        else:  # balanced
            # Price between average and median for balanced approach
            median_competitor = np.median(competitor_prices)
            optimal_price = (avg_competitor + median_competitor) / 2
            rationale = "Balanced pricing between average and median"
        
        # Ensure minimum profit margin
        min_acceptable_price = cost_price * (1 + self.profit_margin_min)
        if optimal_price < min_acceptable_price:
            optimal_price = min_acceptable_price
            rationale += f" (adjusted for minimum {self.profit_margin_min*100}% margin)"
        
        return optimal_price, rationale
    
    def generate_pricing_strategies(self, 
                                  cost_price: float,
                                  competitor_prices: List[float],
                                  product_category: str) -> List[PricingStrategy]:
        """Generate multiple pricing strategies"""
        strategies = []
        
        # Strategy 1: Penetration Pricing
        penetration_price, penetration_rationale = self.calculate_optimal_price(
            cost_price, competitor_prices, "penetration"
        )
        
        strategies.append(PricingStrategy(
            strategy_name="Market Penetration",
            recommended_price=penetration_price,
            rationale=penetration_rationale,
            competitive_position="Low/Aggressive",
            profit_margin=(penetration_price - cost_price) / cost_price,
            confidence_score=0.7,
            risk_level="Medium-High",
            implementation_notes=[
                "Monitor competitor responses closely",
                "Plan for potential price wars",
                "Focus on volume-based profitability"
            ]
        ))
        
        # Strategy 2: Competitive Pricing
        competitive_price, competitive_rationale = self.calculate_optimal_price(
            cost_price, competitor_prices, "competitive"
        )
        
        strategies.append(PricingStrategy(
            strategy_name="Competitive Parity",
            recommended_price=competitive_price,
            rationale=competitive_rationale,
            competitive_position="Market Average",
            profit_margin=(competitive_price - cost_price) / cost_price,
            confidence_score=0.8,
            risk_level="Low-Medium",
            implementation_notes=[
                "Safe middle-ground approach",
                "Monitor market trends regularly",
                "Differentiate through non-price factors"
            ]
        ))
        
        # Strategy 3: Premium Pricing
        premium_price, premium_rationale = self.calculate_optimal_price(
            cost_price, competitor_prices, "premium"
        )
        
        strategies.append(PricingStrategy(
            strategy_name="Premium Positioning",
            recommended_price=premium_price,
            rationale=premium_rationale,
            competitive_position="High/Premium",
            profit_margin=(premium_price - cost_price) / cost_price,
            confidence_score=0.6,
            risk_level="Medium",
            implementation_notes=[
                "Justify premium with superior features/service",
                "Target quality-conscious customers",
                "Invest in brand building"
            ]
        ))
        
        # Strategy 4: Dynamic/Balanced
        balanced_price, balanced_rationale = self.calculate_optimal_price(
            cost_price, competitor_prices, "balanced"
        )
        
        strategies.append(PricingStrategy(
            strategy_name="Dynamic Balanced",
            recommended_price=balanced_price,
            rationale=balanced_rationale,
            competitive_position="Optimal Balance",
            profit_margin=(balanced_price - cost_price) / cost_price,
            confidence_score=0.85,
            risk_level="Low",
            implementation_notes=[
                "Best overall risk-reward ratio",
                "Flexible for market changes",
                "Monitor and adjust regularly"
            ]
        ))
        
        return sorted(strategies, key=lambda x: x.confidence_score, reverse=True)
    
    def simulate_market_scenarios(self, 
                                base_price: float,
                                competitor_prices: List[float],
                                estimated_demand: int = 1000) -> List[MarketScenario]:
        """Simulate different market scenarios"""
        
        scenarios = []
        
        # Base Scenario
        base_scenario = MarketScenario(
            scenario_name="Base Case",
            probability=0.6,
            price_impact=1.0,
            volume_impact=1.0,
            revenue_projection=base_price * estimated_demand
        )
        scenarios.append(base_scenario)
        
        # Optimistic Scenario
        optimistic_scenario = MarketScenario(
            scenario_name="Optimistic",
            probability=0.2,
            price_impact=1.05,  # 5% price premium possible
            volume_impact=1.3,  # 30% volume increase
            revenue_projection=base_price * 1.05 * estimated_demand * 1.3
        )
        scenarios.append(optimistic_scenario)
        
        # Pessimistic Scenario  
        pessimistic_scenario = MarketScenario(
            scenario_name="Pessimistic",
            probability=0.2,
            price_impact=0.9,   # 10% price reduction needed
            volume_impact=0.7,  # 30% volume decrease
            revenue_projection=base_price * 0.9 * estimated_demand * 0.7
        )
        scenarios.append(pessimistic_scenario)
        
        return scenarios
    
    def calculate_price_elasticity(self, 
                                 historical_prices: List[float],
                                 historical_volumes: List[int]) -> float:
        """Calculate price elasticity of demand"""
        if len(historical_prices) < 2 or len(historical_volumes) < 2:
            return -1.5  # Default elasticity for electronics
        
        try:
            # Calculate percentage changes
            price_changes = []
            volume_changes = []
            
            for i in range(1, len(historical_prices)):
                price_change = (historical_prices[i] - historical_prices[i-1]) / historical_prices[i-1]
                volume_change = (historical_volumes[i] - historical_volumes[i-1]) / historical_volumes[i-1]
                
                if price_change != 0:  # Avoid division by zero
                    price_changes.append(price_change)
                    volume_changes.append(volume_change)
            
            if not price_changes:
                return -1.5
            
            # Calculate elasticity as average of volume change / price change
            elasticities = [vol_change / price_change for vol_change, price_change in 
                          zip(volume_changes, price_changes) if price_change != 0]
            
            return np.mean(elasticities) if elasticities else -1.5
            
        except Exception as e:
            logger.warning(f"Error calculating price elasticity: {e}")
            return -1.5  # Default elasticity
    
    def assess_pricing_risk(self, 
                          recommended_price: float,
                          competitor_prices: List[float],
                          market_position: str) -> Dict[str, any]:
        """Assess risks associated with pricing strategy"""
        
        risks = {
            "overall_risk": "Low",
            "risk_factors": [],
            "mitigation_strategies": []
        }
        
        if not competitor_prices:
            risks["risk_factors"].append("Limited competitive intelligence")
            risks["mitigation_strategies"].append("Invest in market research")
            risks["overall_risk"] = "Medium"
        
        # Price positioning risks
        avg_competitor_price = np.mean(competitor_prices) if competitor_prices else recommended_price
        
        if recommended_price > avg_competitor_price * 1.2:
            risks["risk_factors"].append("Significant premium over competition")
            risks["mitigation_strategies"].append("Ensure clear value differentiation")
            risks["overall_risk"] = "High" if risks["overall_risk"] != "High" else "High"
        
        elif recommended_price < avg_competitor_price * 0.8:
            risks["risk_factors"].append("Aggressive pricing may trigger price war")
            risks["mitigation_strategies"].append("Monitor competitor reactions closely")
            risks["overall_risk"] = "Medium-High"
        
        # Market position risks
        if market_position == "premium":
            risks["risk_factors"].append("Premium positioning requires brand strength")
            risks["mitigation_strategies"].append("Invest in brand building and quality")
        
        elif market_position == "penetration":
            risks["risk_factors"].append("Low margins may impact profitability")
            risks["mitigation_strategies"].append("Focus on operational efficiency")
        
        return risks
    
    def recommend_pricing_adjustments(self, 
                                    current_performance: Dict[str, float],
                                    target_metrics: Dict[str, float]) -> List[str]:
        """Recommend pricing adjustments based on performance"""
        
        recommendations = []
        
        # Revenue performance
        if current_performance.get("revenue", 0) < target_metrics.get("revenue", 0):
            if current_performance.get("volume", 0) < target_metrics.get("volume", 0):
                recommendations.append("Consider price reduction to stimulate demand")
            else:
                recommendations.append("Volume is good, consider slight price increase")
        
        # Margin performance
        if current_performance.get("margin", 0) < target_metrics.get("margin", 0):
            recommendations.append("Margins below target - evaluate cost optimization or price increase")
        
        # Market share performance
        if current_performance.get("market_share", 0) < target_metrics.get("market_share", 0):
            recommendations.append("Consider competitive pricing or promotional campaigns")
        
        # Seasonal adjustments
        current_month = datetime.now().month
        if current_month in [11, 12, 1]:  # Holiday season
            recommendations.append("Consider holiday pricing strategy")
        elif current_month in [6, 7, 8]:  # Summer season
            recommendations.append("Evaluate seasonal demand patterns")
        
        return recommendations if recommendations else ["Current pricing appears optimal"]