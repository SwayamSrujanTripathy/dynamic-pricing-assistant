"""
Price Optimization Agent using Gemini 2.0 Flash
Optimizes pricing strategies based on competitor data and market analysis
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import google.generativeai as genai
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceOptimizationAgent:
    def __init__(self, gemini_api_key: str):
        """
        Initialize the price optimization agent with Gemini 2.0 Flash
        
        Args:
            gemini_api_key: Google Gemini API key
        """
        self.gemini_api_key = gemini_api_key
        genai.configure(api_key=gemini_api_key)
        
        # Initialize Gemini model (using flash for CPU efficiency)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        self.scaler = StandardScaler()
        self.price_model = None
        self.optimization_history = []
        
    def load_competitor_data(self, data_source) -> pd.DataFrame:
        """
        Load competitor data from various sources
        
        Args:
            data_source: Can be DataFrame, CSV file path, or dictionary
            
        Returns:
            Processed DataFrame with competitor data
        """
        if isinstance(data_source, pd.DataFrame):
            df = data_source.copy()
        elif isinstance(data_source, str):
            df = pd.read_csv(data_source)
        elif isinstance(data_source, dict):
            df = pd.DataFrame(data_source)
        else:
            raise ValueError("Data source must be DataFrame, CSV path, or dictionary")
        
        # Clean and preprocess data
        df = self._preprocess_data(df)
        
        return df
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and preprocess competitor data
        
        Args:
            df: Raw competitor data
            
        Returns:
            Cleaned DataFrame
        """
        # Remove rows with missing prices
        df = df.dropna(subset=['price'])
        
        # Convert price to numeric if it's string
        if df['price'].dtype == 'object':
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
        
        # Remove outliers (prices beyond 3 standard deviations)
        price_mean = df['price'].mean()
        price_std = df['price'].std()
        df = df[abs(df['price'] - price_mean) <= 3 * price_std]
        
        # Add derived features
        df['price_category'] = pd.cut(df['price'], bins=5, labels=['Budget', 'Low', 'Medium', 'High', 'Premium'])
        
        return df
    
    def analyze_market_position(self, df: pd.DataFrame, your_products: List[Dict]) -> Dict:
        """
        Analyze market position using Gemini AI
        
        Args:
            df: Competitor data DataFrame
            your_products: List of your product dictionaries with name, price, features
            
        Returns:
            Market position analysis
        """
        # Prepare competitor summary
        competitor_summary = df.groupby('competitor_name').agg({
            'price': ['mean', 'min', 'max', 'count']
        }).to_string()
        
        # Prepare your products summary
        your_products_str = json.dumps(your_products, indent=2)
        
        prompt = f"""
        Analyze the market position based on competitor data and our product lineup:
        
        COMPETITOR DATA SUMMARY:
        {competitor_summary}
        
        OUR PRODUCTS:
        {your_products_str}
        
        COMPETITOR PRODUCT SAMPLE:
        {df.head(10)[['name', 'price', 'competitor_name']].to_string()}
        
        Please provide a comprehensive market position analysis including:
        
        1. COMPETITIVE POSITIONING:
           - Where do our products stand in the market?
           - Are we priced competitively?
           - Which competitors are our main threats?
        
        2. PRICING GAPS:
           - What price ranges are underserved?
           - Where are opportunities for new products?
        
        3. MARKET INSIGHTS:
           - What are the pricing trends?
           - Which price categories have most competition?
        
        4. STRATEGIC RECOMMENDATIONS:
           - Should we adjust our pricing?
           - What pricing strategies should we consider?
        
        Format your response as actionable business insights.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            return {
                'analysis': response.text,
                'market_stats': {
                    'competitor_count': df['competitor_name'].nunique(),
                    'avg_competitor_price': df['price'].mean(),
                    'price_range': {
                        'min': df['price'].min(),
                        'max': df['price'].max()
                    },
                    'your_products_count': len(your_products),
                    'your_avg_price': np.mean([p['price'] for p in your_products])
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in market analysis: {str(e)}")
            return {"error": f"Market analysis failed: {str(e)}"}
    
    def optimize_pricing_strategy(self, df: pd.DataFrame, your_products: List[Dict], 
                                business_constraints: Dict = None) -> Dict:
        """
        Generate optimized pricing strategy using Gemini AI and statistical analysis
        
        Args:
            df: Competitor data DataFrame
            your_products: List of your product dictionaries
            business_constraints: Dictionary with min_margin, max_price, etc.
            
        Returns:
            Optimized pricing recommendations
        """
        if business_constraints is None:
            business_constraints = {
                'min_margin_percent': 20,
                'max_price_increase': 0.15,
                'target_market_share': 'medium'
            }
        
        # Statistical analysis
        price_stats = self._calculate_price_statistics(df)
        
        # Competitive analysis
        competitive_gaps = self._find_competitive_gaps(df, your_products)
        
        # Prepare comprehensive data for Gemini
        analysis_data = {
            'price_statistics': price_stats,
            'competitive_gaps': competitive_gaps,
            'your_products': your_products,
            'business_constraints': business_constraints,
            'competitor_sample': df.head(15).to_dict('records')
        }
        
        prompt = f"""
        Based on the following comprehensive market data, provide optimized pricing recommendations:
        
        MARKET STATISTICS:
        - Average competitor price: ${price_stats['mean']:.2f}
        - Price range: ${price_stats['min']:.2f} - ${price_stats['max']:.2f}
        - Most common price range: ${price_stats['mode_range']}
        
        COMPETITIVE GAPS:
        {json.dumps(competitive_gaps, indent=2)}
        
        YOUR CURRENT PRODUCTS:
        {json.dumps(your_products, indent=2)}
        
        BUSINESS CONSTRAINTS:
        {json.dumps(business_constraints, indent=2)}
        
        COMPETITOR SAMPLE DATA:
        {json.dumps(analysis_data['competitor_sample'][:5], indent=2)}
        
        Please provide detailed pricing optimization recommendations in the following format:
        
        1. INDIVIDUAL PRODUCT RECOMMENDATIONS:
           For each of our products, suggest:
           - Optimal price point
           - Reasoning for the recommendation
           - Expected market position
           - Risk assessment
        
        2. PORTFOLIO STRATEGY:
           - Overall pricing strategy
           - Product positioning recommendations
           - Cross-selling opportunities
        
        3. COMPETITIVE RESPONSE:
           - How to respond to competitor pricing
           - Defensive pricing strategies
           - Market penetration tactics
        
        4. IMPLEMENTATION PLAN:
           - Phased rollout recommendations
           - Monitoring metrics
           - Success indicators
        
        Be specific with price recommendations and provide clear reasoning for each suggestion.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Also generate quantitative recommendations
            quantitative_recs = self._generate_statistical_recommendations(df, your_products, business_constraints)
            
            optimization_result = {
                'ai_recommendations': response.text,
                'quantitative_analysis': quantitative_recs,
                'market_data': price_stats,
                'competitive_gaps': competitive_gaps,
                'generated_at': datetime.now().isoformat()
            }
            
            self.optimization_history.append(optimization_result)
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Error in pricing optimization: {str(e)}")
            return {"error": f"Pricing optimization failed: {str(e)}"}
    
    def _calculate_price_statistics(self, df: pd.DataFrame) -> Dict:
        """Calculate statistical measures of competitor pricing"""
        return {
            'mean': df['price'].mean(),
            'median': df['price'].median(),
            'std': df['price'].std(),
            'min': df['price'].min(),
            'max': df['price'].max(),
            'q25': df['price'].quantile(0.25),
            'q75': df['price'].quantile(0.75),
            'mode_range': f"${df['price'].quantile(0.4):.2f} - ${df['price'].quantile(0.6):.2f}"
        }
    
    def _find_competitive_gaps(self, df: pd.DataFrame, your_products: List[Dict]) -> Dict:
        """Identify pricing gaps in the market"""
        competitor_prices = sorted(df['price'].unique())
        your_prices = [p['price'] for p in your_products]
        
        # Find gaps where competitors have products but we don't
        gaps = []
        for i in range(len(competitor_prices) - 1):
            gap_start = competitor_prices[i]
            gap_end = competitor_prices[i + 1]
            gap_size = gap_end - gap_start
            
            # Check if we have products in this range
            has_product_in_range = any(gap_start <= price <= gap_end for price in your_prices)
            
            if not has_product_in_range and gap_size > 50:  # Significant gap
                gaps.append({
                    'range': f"${gap_start:.2f} - ${gap_end:.2f}",
                    'gap_size': gap_size,
                    'opportunity_score': min(gap_size / 100, 10)  # Normalize to 0-10
                })
        
        return {
            'pricing_gaps': gaps,
            'underserved_ranges': [gap for gap in gaps if gap['opportunity_score'] > 3]
        }
    
    def _generate_statistical_recommendations(self, df: pd.DataFrame, 
                                            your_products: List[Dict], 
                                            constraints: Dict) -> Dict:
        """Generate quantitative pricing recommendations"""
        recommendations = []
        
        for product in your_products:
            current_price = product['price']
            
            # Find similar competitor products (simplified similarity)
            similar_products = df[
                df['name'].str.contains(product['name'].split()[0], case=False, na=False)
            ]
            
            if len(similar_products) > 0:
                competitor_avg = similar_products['price'].mean()
                competitor_median = similar_products['price'].median()
                
                # Calculate recommended price based on market position
                if constraints.get('target_market_share') == 'high':
                    # Aggressive pricing for market share
                    recommended_price = competitor_median * 0.95
                elif constraints.get('target_market_share') == 'premium':
                    # Premium positioning
                    recommended_price = competitor_avg * 1.15
                else:
                    # Competitive positioning
                    recommended_price = competitor_median * 1.02
                
                # Apply business constraints
                min_price = current_price * (1 + constraints.get('min_margin_percent', 20) / 100)
                max_increase = current_price * (1 + constraints.get('max_price_increase', 0.15))
                
                recommended_price = max(min_price, min(recommended_price, max_increase))
                
                recommendations.append({
                    'product_name': product['name'],
                    'current_price': current_price,
                    'recommended_price': round(recommended_price, 2),
                    'price_change': round(recommended_price - current_price, 2),
                    'change_percent': round((recommended_price - current_price) / current_price * 100, 2),
                    'competitor_average': round(competitor_avg, 2),
                    'market_position': 'competitive' if abs(recommended_price - competitor_median) < 10 else 'differentiated'
                })
        
        return {
            'product_recommendations': recommendations,
            'portfolio_summary': {
                'total_products': len(recommendations),
                'avg_price_change': np.mean([r['change_percent'] for r in recommendations]),
                'products_with_increases': len([r for r in recommendations if r['price_change'] > 0])
            }
        }
    
    def simulate_pricing_impact(self, current_products: List[Dict], 
                              new_pricing: List[Dict], 
                              market_elasticity: float = -1.5) -> Dict:
        """
        Simulate the impact of pricing changes
        
        Args:
            current_products: Current product pricing
            new_pricing: Proposed new pricing
            market_elasticity: Price elasticity of demand (default -1.5)
            
        Returns:
            Impact simulation results
        """
        simulations = []
        
        for current, new in zip(current_products, new_pricing):
            price_change_percent = (new['price'] - current['price']) / current['price']
            
            # Estimate demand change using elasticity
            demand_change_percent = price_change_percent * market_elasticity
            
            # Estimate revenue impact
            current_revenue = current['price'] * current.get('monthly_volume', 100)
            new_volume = current.get('monthly_volume', 100) * (1 + demand_change_percent)
            new_revenue = new['price'] * new_volume
            
            revenue_change = new_revenue - current_revenue
            
            simulations.append({
                'product_name': current['name'],
                'price_change_percent': round(price_change_percent * 100, 2),
                'estimated_volume_change_percent': round(demand_change_percent * 100, 2),
                'current_revenue': round(current_revenue, 2),
                'projected_revenue': round(new_revenue, 2),
                'revenue_change': round(revenue_change, 2),
                'revenue_change_percent': round(revenue_change / current_revenue * 100, 2)
            })
        
        # Prepare simulation summary for Gemini analysis
        simulation_summary = json.dumps(simulations, indent=2)
        
        prompt = f"""
        Analyze the following pricing impact simulation and provide insights:
        
        SIMULATION RESULTS:
        {simulation_summary}
        
        Market Elasticity Used: {market_elasticity}
        
        Please provide analysis on:
        1. Overall portfolio impact
        2. Risk assessment for each product
        3. Recommended implementation approach
        4. Key metrics to monitor
        5. Potential market reactions
        
        Focus on actionable insights for business decision-making.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            return {
                'simulation_results': simulations,
                'ai_analysis': response.text,
                'summary_metrics': {
                    'total_products': len(simulations),
                    'avg_price_change': np.mean([s['price_change_percent'] for s in simulations]),
                    'total_revenue_impact': sum([s['revenue_change'] for s in simulations]),
                    'products_with_positive_impact': len([s for s in simulations if s['revenue_change'] > 0])
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in impact simulation: {str(e)}")
            return {"error": f"Impact simulation failed: {str(e)}"}
    
    def generate_pricing_report(self, save_to_file: bool = True) -> Dict:
        """
        Generate comprehensive pricing optimization report
        
        Args:
            save_to_file: Whether to save report to file
            
        Returns:
            Complete pricing report
        """
        if not self.optimization_history:
            return {"error": "No optimization history available"}
        
        latest_optimization = self.optimization_history[-1]
        
        report = {
            'report_generated_at': datetime.now().isoformat(),
            'optimization_summary': latest_optimization,
            'historical_optimizations': len(self.optimization_history),
            'recommendations_summary': self._summarize_recommendations()
        }
        
        if save_to_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pricing_optimization_report_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Report saved to {filename}")
            report['saved_to'] = filename
        
        return report
    
    def _summarize_recommendations(self) -> Dict:
        """Summarize key recommendations from optimization history"""
        if not self.optimization_history:
            return {}
        
        latest = self.optimization_history[-1]
        quantitative = latest.get('quantitative_analysis', {})
        
        return {
            'key_insights': "Check AI recommendations in the full report",
            'products_analyzed': quantitative.get('portfolio_summary', {}).get('total_products', 0),
            'avg_recommended_change': quantitative.get('portfolio_summary', {}).get('avg_price_change', 0),
            'optimization_date': latest.get('generated_at')
        }

# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = PriceOptimizationAgent("your-gemini-api-key")
    
    # Example competitor data
    competitor_data = pd.DataFrame([
        {'name': 'Laptop Pro', 'price': 1200, 'competitor_name': 'TechCorp'},
        {'name': 'Gaming Laptop', 'price': 1500, 'competitor_name': 'GameTech'},
        {'name': 'Business Laptop', 'price': 900, 'competitor_name': 'BizTech'}
    ])
    
    # Your products
    your_products = [
        {'name': 'Laptop Elite', 'price': 1100, 'monthly_volume': 50},
        {'name': 'Gaming Beast', 'price': 1400, 'monthly_volume': 30}
    ]
    
    # Analyze market position
    market_analysis = agent.analyze_market_position(competitor_data, your_products)
    print("Market Analysis:", market_analysis['analysis'][:200] + "...")
    
    # Optimize pricing
    optimization = agent.optimize_pricing_strategy(competitor_data, your_products)
    print("Optimization Results:", optimization['quantitative_analysis'])
    
    # Generate pricing report
    report = agent.generate_pricing_report()
    print(f"Report generated and saved to: {report.get('saved_to', 'memory only')}")