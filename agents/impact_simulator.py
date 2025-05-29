"""
Impact Simulation Agent using Gemini 2.0 Flash
Simulates the impact of pricing changes on business metrics
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import google.generativeai as genai
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImpactSimulationAgent:
    def __init__(self, gemini_api_key: str):
        """
        Initialize the impact simulation agent with Gemini 2.0 Flash
        
        Args:
            gemini_api_key: Google Gemini API key
        """
        self.gemini_api_key = gemini_api_key
        genai.configure(api_key=gemini_api_key)
        
        # Initialize Gemini model (using flash for CPU efficiency)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        self.simulation_history = []
        self.baseline_data = None
        
    def set_baseline_data(self, baseline_data: Dict):
        """
        Set baseline business metrics for comparison
        
        Args:
            baseline_data: Dictionary containing current business metrics
        """
        required_fields = ['products', 'monthly_revenue', 'customer_segments', 'market_share']
        
        for field in required_fields:
            if field not in baseline_data:
                logger.warning(f"Missing baseline field: {field}")
        
        self.baseline_data = {
            'timestamp': datetime.now().isoformat(),
            **baseline_data
        }
        
        logger.info("Baseline data set successfully")
    
    def simulate_demand_impact(self, pricing_changes: List[Dict], 
                             market_conditions: Dict = None) -> Dict:
        """
        Simulate demand impact of pricing changes
        
        Args:
            pricing_changes: List of pricing change dictionaries
            market_conditions: Market elasticity and external factors
            
        Returns:
            Demand simulation results
        """
        if market_conditions is None:
            market_conditions = {
                'price_elasticity': -1.2,
                'income_elasticity': 0.8,
                'cross_elasticity': -0.3,
                'seasonal_factor': 1.0,
                'competitive_response': 'moderate'
            }
        
        simulations = []
        
        for change in pricing_changes:
            # Calculate base demand change using price elasticity
            price_change_percent = change['price_change_percent'] / 100
            base_demand_change = price_change_percent * market_conditions['price_elasticity']
            
            # Apply market condition adjustments
            seasonal_adjustment = market_conditions.get('seasonal_factor', 1.0) - 1
            competitive_adjustment = self._calculate_competitive_adjustment(
                market_conditions.get('competitive_response', 'moderate')
            )
            
            total_demand_change = base_demand_change + seasonal_adjustment + competitive_adjustment
            
            # Calculate new volumes and metrics
            current_volume = change.get('current_monthly_volume', 100)
            new_volume = current_volume * (1 + total_demand_change)
            
            current_revenue = change['current_price'] * current_volume
            new_revenue = change['new_price'] * new_volume
            
            simulation_result = {
                'product_name': change['product_name'],
                'price_change_percent': change['price_change_percent'],
                'demand_change_percent': round(total_demand_change * 100, 2),
                'current_volume': current_volume,
                'projected_volume': round(new_volume, 0),
                'volume_change': round(new_volume - current_volume, 0),
                'current_revenue': round(current_revenue, 2),
                'projected_revenue': round(new_revenue, 2),
                'revenue_change': round(new_revenue - current_revenue, 2),
                'revenue_change_percent': round((new_revenue - current_revenue) / current_revenue * 100, 2),
                'elasticity_factors': {
                    'base_elasticity': market_conditions['price_elasticity'],
                    'seasonal_adjustment': seasonal_adjustment,
                    'competitive_adjustment': competitive_adjustment
                }
            }
            
            simulations.append(simulation_result)
        
        return {
            'simulations': simulations,
            'market_conditions': market_conditions,
            'aggregate_impact': self._calculate_aggregate_impact(simulations),
            'generated_at': datetime.now().isoformat()
        }
    
    def _calculate_competitive_adjustment(self, response_level: str) -> float:
        """Calculate competitive response adjustment factor"""
        adjustments = {
            'none': 0.0,
            'low': -0.02,
            'moderate': -0.05,
            'high': -0.10,
            'aggressive': -0.15
        }
        return adjustments.get(response_level.lower(), -0.05)
    
    def _calculate_aggregate_impact(self, simulations: List[Dict]) -> Dict:
        """Calculate aggregate impact across all products"""
        total_current_revenue = sum([s['current_revenue'] for s in simulations])
        total_projected_revenue = sum([s['projected_revenue'] for s in simulations])
        total_volume_change = sum([s['volume_change'] for s in simulations])
        
        return {
            'total_revenue_change': round(total_projected_revenue - total_current_revenue, 2),
            'total_revenue_change_percent': round((total_projected_revenue - total_current_revenue) / total_current_revenue * 100, 2),
            'total_volume_change': total_volume_change,
            'products_with_positive_impact': len([s for s in simulations if s['revenue_change'] > 0]),
            'products_with_negative_impact': len([s for s in simulations if s['revenue_change'] < 0]),
            'average_price_change': np.mean([s['price_change_percent'] for s in simulations])
        }
    
    def simulate_customer_segment_impact(self, pricing_changes: List[Dict], 
                                       customer_segments: List[Dict]) -> Dict:
        """
        Simulate impact on different customer segments
        
        Args:
            pricing_changes: List of pricing changes
            customer_segments: List of customer segment definitions
            
        Returns:
            Customer segment impact analysis
        """
        segment_impacts = []
        
        for segment in customer_segments:
            segment_name = segment['name']
            price_sensitivity = segment.get('price_sensitivity', 'medium')
            segment_size = segment.get('size_percent', 25)
            
            # Calculate segment-specific elasticity
            elasticity_map = {
                'low': -0.8,
                'medium': -1.2,
                'high': -1.8,
                'very_high': -2.5
            }
            segment_elasticity = elasticity_map.get(price_sensitivity, -1.2)
            
            segment_impact = {
                'segment_name': segment_name,
                'segment_size_percent': segment_size,
                'price_sensitivity': price_sensitivity,
                'elasticity': segment_elasticity,
                'product_impacts': []
            }
            
            for change in pricing_changes:
                price_change_percent = change['price_change_percent'] / 100
                demand_change = price_change_percent * segment_elasticity
                
                # Calculate segment contribution to overall impact
                segment_volume_impact = demand_change * (segment_size / 100)
                
                product_impact = {
                    'product_name': change['product_name'],
                    'segment_demand_change_percent': round(demand_change * 100, 2),
                    'segment_contribution_to_total': round(segment_volume_impact * 100, 2),
                    'risk_level': self._assess_segment_risk(demand_change, price_sensitivity)
                }
                
                segment_impact['product_impacts'].append(product_impact)
            
            segment_impacts.append(segment_impact)
        
        return {
            'segment_impacts': segment_impacts,
            'overall_risk_assessment': self._assess_overall_segment_risk(segment_impacts),
            'generated_at': datetime.now().isoformat()
        }
    
    def _assess_segment_risk(self, demand_change: float, sensitivity: str) -> str:
        """Assess risk level for a customer segment"""
        if abs(demand_change) < 0.05:
            return 'low'
        elif abs(demand_change) < 0.15:
            return 'medium'
        elif abs(demand_change) < 0.25:
            return 'high'
        else:
            return 'very_high'
    
    def _assess_overall_segment_risk(self, segment_impacts: List[Dict]) -> Dict:
        """Assess overall risk across all segments"""
        high_risk_segments = [s for s in segment_impacts 
                             if any(p['risk_level'] in ['high', 'very_high'] 
                                   for p in s['product_impacts'])]
        
        return {
            'high_risk_segment_count': len(high_risk_segments),
            'high_risk_segments': [s['segment_name'] for s in high_risk_segments],
            'overall_risk_level': 'high' if len(high_risk_segments) > len(segment_impacts) / 2 else 'medium'
        }
    
    def simulate_competitive_response(self, pricing_changes: List[Dict], 
                                    competitor_profiles: List[Dict]) -> Dict:
        """
        Simulate potential competitive responses to pricing changes
        
        Args:
            pricing_changes: List of pricing changes
            competitor_profiles: List of competitor characteristics
            
        Returns:
            Competitive response simulation
        """
        response_scenarios = []
        
        for competitor in competitor_profiles:
            competitor_name = competitor['name']
            aggressiveness = competitor.get('aggressiveness', 'medium')
            market_share = competitor.get('market_share_percent', 20)
            response_speed = competitor.get('response_speed_days', 30)
            
            competitor_responses = []
            
            for change in pricing_changes:
                # Determine likelihood of response based on price change magnitude
                price_change_magnitude = abs(change['price_change_percent'])
                
                response_probability = self._calculate_response_probability(
                    price_change_magnitude, aggressiveness, market_share
                )
                
                if response_probability > 0.3:  # Significant probability of response
                    # Estimate competitor's likely response
                    competitor_response = self._estimate_competitor_response(
                        change, aggressiveness, market_share
                    )
                    
                    competitor_responses.append({
                        'product_category': change['product_name'],
                        'response_probability': round(response_probability, 2),
                        'estimated_response_percent': competitor_response['response_percent'],
                        'response_timeframe_days': response_speed,
                        'impact_on_our_demand': competitor_response['impact_on_us'],
                        'response_type': competitor_response['type']
                    })
            
            if competitor_responses:
                response_scenarios.append({
                    'competitor_name': competitor_name,
                    'aggressiveness_level': aggressiveness,
                    'market_share_percent': market_share,
                    'responses': competitor_responses
                })
        
        return {
            'competitive_scenarios': response_scenarios,
            'summary': self._summarize_competitive_impact(response_scenarios),
            'generated_at': datetime.now().isoformat()
        }
    
    def _calculate_response_probability(self, price_change_magnitude: float, 
                                      aggressiveness: str, market_share: float) -> float:
        """Calculate probability of competitive response"""
        base_probability = min(price_change_magnitude / 20, 0.8)  # Max 80% for 20%+ price changes
        
        # Adjust for aggressiveness
        aggressiveness_multiplier = {
            'low': 0.7,
            'medium': 1.0,
            'high': 1.3,
            'very_high': 1.6
        }.get(aggressiveness, 1.0)
        
        # Adjust for market share (larger players more likely to respond)
        market_share_multiplier = 1 + (market_share / 100)
        
        probability = base_probability * aggressiveness_multiplier * market_share_multiplier
        return min(probability, 0.95)  # Cap at 95%
    
    def _estimate_competitor_response(self, change: Dict, aggressiveness: str, 
                                    market_share: float) -> Dict:
        """Estimate competitor's likely response to our pricing change"""
        our_change_percent = change['price_change_percent']
        
        # Estimate response magnitude based on aggressiveness
        response_ratios = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.9,
            'very_high': 1.2
        }
        
        response_ratio = response_ratios.get(aggressiveness, 0.6)
        competitor_response_percent = our_change_percent * response_ratio
        
        # Determine response type
        if our_change_percent > 0:  # We increased prices
            response_type = 'follow_increase' if competitor_response_percent > 0 else 'maintain_price'
        else:  # We decreased prices
            response_type = 'follow_decrease' if competitor_response_percent < 0 else 'price_war'
        
        # Estimate impact on our demand
        impact_magnitude = abs(competitor_response_percent) * (market_share / 100) * 0.5
        impact_on_us = -impact_magnitude if competitor_response_percent * our_change_percent < 0 else impact_magnitude
        
        return {
            'response_percent': round(competitor_response_percent, 2),
            'type': response_type,
            'impact_on_us': round(impact_on_us, 3)
        }
    
    def _summarize_competitive_impact(self, scenarios: List[Dict]) -> Dict:
        """Summarize overall competitive impact"""
        total_scenarios = sum(len(s['responses']) for s in scenarios)
        high_probability_responses = sum(
            len([r for r in s['responses'] if r['response_probability'] > 0.7]) 
            for s in scenarios
        )
        
        return {
            'total_competitive_scenarios': total_scenarios,
            'high_probability_responses': high_probability_responses,
            'competitive_risk_level': 'high' if high_probability_responses > total_scenarios * 0.5 else 'medium'
        }
    
    def run_monte_carlo_simulation(self, pricing_changes: List[Dict], 
                                 uncertainty_ranges: Dict, 
                                 num_simulations: int = 1000) -> Dict:
        """
        Run Monte Carlo simulation for pricing impact with uncertainty
        
        Args:
            pricing_changes: List of pricing changes
            uncertainty_ranges: Ranges for uncertain parameters
            num_simulations: Number of simulation runs
            
        Returns:
            Monte Carlo simulation results
        """
        results = []
        
        for _ in range(num_simulations):
            # Sample random values for uncertain parameters
            elasticity = np.random.normal(
                uncertainty_ranges.get('elasticity_mean', -1.2),
                uncertainty_ranges.get('elasticity_std', 0.3)
            )
            
            seasonal_factor = np.random.normal(
                uncertainty_ranges.get('seasonal_mean', 1.0),
                uncertainty_ranges.get('seasonal_std', 0.1)
            )
            
            competitive_intensity = np.random.uniform(
                uncertainty_ranges.get('competitive_min', 0.0),
                uncertainty_ranges.get('competitive_max', 0.2)
            )
            
            # Run simulation with sampled parameters
            simulation_revenue = 0
            for change in pricing_changes:
                price_change_percent = change['price_change_percent'] / 100
                demand_change = (price_change_percent * elasticity * seasonal_factor) - competitive_intensity
                
                current_volume = change.get('current_monthly_volume', 100)
                new_volume = current_volume * (1 + demand_change)
                revenue = change['new_price'] * new_volume
                simulation_revenue += revenue
            
            results.append(simulation_revenue)
        
        # Calculate statistics
        results_array = np.array(results)
        
        return {
            'simulation_runs': num_simulations,
            'revenue_statistics': {
                'mean': round(np.mean(results_array), 2),
                'median': round(np.median(results_array), 2),
                'std': round(np.std(results_array), 2),
                'min': round(np.min(results_array), 2),
                'max': round(np.max(results_array), 2),
                'percentile_5': round(np.percentile(results_array, 5), 2),
                'percentile_95': round(np.percentile(results_array, 95), 2)
            },
            'risk_metrics': {
                'probability_of_loss': round(np.mean(results_array < 0), 3),
                'value_at_risk_5pct': round(np.percentile(results_array, 5), 2),
                'coefficient_of_variation': round(np.std(results_array) / np.mean(results_array), 3)
            },
            'generated_at': datetime.now().isoformat()
        }
    
    def generate_comprehensive_impact_report(self, pricing_changes: List[Dict],
                                           market_conditions: Dict = None,
                                           customer_segments: List[Dict] = None,
                                           competitor_profiles: List[Dict] = None) -> Dict:
        """
        Generate comprehensive impact analysis using Gemini AI
        
        Args:
            pricing_changes: List of pricing changes to analyze
            market_conditions: Market elasticity and conditions
            customer_segments: Customer segment definitions
            competitor_profiles: Competitor characteristics
            
        Returns:
            Comprehensive impact report
        """
        # Run all simulations
        demand_impact = self.simulate_demand_impact(pricing_changes, market_conditions)
        
        segment_impact = None
        if customer_segments:
            segment_impact = self.simulate_customer_segment_impact(pricing_changes, customer_segments)
        
        competitive_impact = None
        if competitor_profiles:
            competitive_impact = self.simulate_competitive_response(pricing_changes, competitor_profiles)
        
        # Monte Carlo simulation with default uncertainty
        uncertainty_ranges = {
            'elasticity_mean': market_conditions.get('price_elasticity', -1.2) if market_conditions else -1.2,
            'elasticity_std': 0.3,
            'seasonal_mean': 1.0,
            'seasonal_std': 0.1,
            'competitive_min': 0.0,
            'competitive_max': 0.15
        }
        monte_carlo = self.run_monte_carlo_simulation(pricing_changes, uncertainty_ranges)
        
        # Prepare comprehensive data for Gemini analysis
        analysis_data = {
            'pricing_changes': pricing_changes,
            'demand_impact': demand_impact,
            'segment_impact': segment_impact,
            'competitive_impact': competitive_impact,
            'monte_carlo_simulation': monte_carlo,
            'baseline_data': self.baseline_data
        }
        
        prompt = f"""
        Analyze the following comprehensive pricing impact simulation and provide strategic insights:
        
        PRICING CHANGES BEING ANALYZED:
        {json.dumps(pricing_changes, indent=2)}
        
        DEMAND IMPACT SIMULATION:
        - Aggregate Revenue Change: {demand_impact['aggregate_impact']['total_revenue_change']}
        - Products with Positive Impact: {demand_impact['aggregate_impact']['products_with_positive_impact']}
        - Products with Negative Impact: {demand_impact['aggregate_impact']['products_with_negative_impact']}
        
        MONTE CARLO RISK ANALYSIS:
        - Expected Revenue (Mean): {monte_carlo['revenue_statistics']['mean']}
        - Revenue Range (5%-95%): {monte_carlo['revenue_statistics']['percentile_5']} to {monte_carlo['revenue_statistics']['percentile_95']}
        - Probability of Loss: {monte_carlo['risk_metrics']['probability_of_loss']}
        - Value at Risk (5%): {monte_carlo['risk_metrics']['value_at_risk_5pct']}
        
        CUSTOMER SEGMENT ANALYSIS:
        {json.dumps(segment_impact, indent=2) if segment_impact else "Not analyzed"}
        
        COMPETITIVE RESPONSE ANALYSIS:
        {json.dumps(competitive_impact, indent=2) if competitive_impact else "Not analyzed"}
        
        Please provide a comprehensive strategic analysis covering:
        
        1. EXECUTIVE SUMMARY:
           - Overall impact assessment
           - Key risks and opportunities
           - Recommended action
        
        2. DETAILED IMPACT ANALYSIS:
           - Revenue and volume implications
           - Customer segment vulnerabilities
           - Competitive risks
        
        3. RISK ASSESSMENT:
           - Probability of success
           - Downside scenarios
           - Mitigation strategies
        
        4. IMPLEMENTATION RECOMMENDATIONS:
           - Phased rollout strategy
           - Monitoring metrics
           - Contingency plans
        
        5. SUCCESS METRICS:
           - KPIs to track
           - Early warning indicators
           - Success thresholds
        
        Provide actionable insights that can guide business decision-making.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            comprehensive_report = {
                'executive_summary': response.text,
                'detailed_analysis': {
                    'demand_simulation': demand_impact,
                    'segment_analysis': segment_impact,
                    'competitive_analysis': competitive_impact,
                    'risk_analysis': monte_carlo
                },
                'key_metrics': {
                    'expected_revenue_change': demand_impact['aggregate_impact']['total_revenue_change'],
                    'expected_revenue_change_percent': demand_impact['aggregate_impact']['total_revenue_change_percent'],
                    'risk_level': self._assess_overall_risk_level(monte_carlo, segment_impact, competitive_impact),
                    'success_probability': 1 - monte_carlo['risk_metrics']['probability_of_loss']
                },
                'generated_at': datetime.now().isoformat()
            }
            
            # Store in history
            self.simulation_history.append(comprehensive_report)
            
            return comprehensive_report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {str(e)}")
            return {"error": f"Report generation failed: {str(e)}"}
    
    def _assess_overall_risk_level(self, monte_carlo: Dict, 
                                 segment_impact: Dict, 
                                 competitive_impact: Dict) -> str:
        """Assess overall risk level from all analyses"""
        risk_factors = []
        
        # Monte Carlo risk
        prob_loss = monte_carlo['risk_metrics']['probability_of_loss']
        if prob_loss > 0.3:
            risk_factors.append('high_monte_carlo')
        elif prob_loss > 0.1:
            risk_factors.append('medium_monte_carlo')
        
        # Segment risk
        if segment_impact and segment_impact.get('overall_risk_assessment', {}).get('overall_risk_level') == 'high':
            risk_factors.append('high_segment')
        
        # Competitive risk
        if competitive_impact and competitive_impact.get('summary', {}).get('competitive_risk_level') == 'high':
            risk_factors.append('high_competitive')
        
        # Determine overall risk
        high_risk_count = len([r for r in risk_factors if 'high' in r])
        
        if high_risk_count >= 2:
            return 'high'
        elif high_risk_count == 1 or len(risk_factors) >= 2:
            return 'medium'
        else:
            return 'low'
    
    def save_simulation_report(self, report: Dict, filename: str = None) -> str:
        """
        Save simulation report to file
        
        Args:
            report: Report dictionary to save
            filename: Optional filename
            
        Returns:
            Saved filename
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"impact_simulation_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Simulation report saved to {filename}")
        return filename
    
    def get_simulation_history_summary(self) -> Dict:
        """Get summary of all simulation history"""
        if not self.simulation_history:
            return {"message": "No simulation history available"}
        
        return {
            'total_simulations': len(self.simulation_history),
            'latest_simulation_date': self.simulation_history[-1]['generated_at'],
            'average_success_probability': np.mean([
                sim['key_metrics']['success_probability'] 
                for sim in self.simulation_history
            ]),
            'risk_level_distribution': {
                'high': len([s for s in self.simulation_history if s['key_metrics']['risk_level'] == 'high']),
                'medium': len([s for s in self.simulation_history if s['key_metrics']['risk_level'] == 'medium']),
                'low': len([s for s in self.simulation_history if s['key_metrics']['risk_level'] == 'low'])
            }
        }

# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = ImpactSimulationAgent("your-gemini-api-key")
    
    # Set baseline data
    baseline = {
        'products': [
            {'name': 'Product A', 'price': 100, 'monthly_volume': 1000},
            {'name': 'Product B', 'price': 150, 'monthly_volume': 500}
        ],
        'monthly_revenue': 125000,
        'customer_segments': ['Premium', 'Standard', 'Budget'],
        'market_share': 15
    }
    agent.set_baseline_data(baseline)
    
    # Define pricing changes
    pricing_changes = [
        {
            'product_name': 'Product A',
            'current_price': 100,
            'new_price': 110,
            'price_change_percent': 10,
            'current_monthly_volume': 1000
        },
        {
            'product_name': 'Product B',
            'current_price': 150,
            'new_price': 140,
            'price_change_percent': -6.67,
            'current_monthly_volume': 500
        }
    ]
    
    # Define customer segments
    customer_segments = [
        {'name': 'Premium', 'price_sensitivity': 'low', 'size_percent': 30},
        {'name': 'Standard', 'price_sensitivity': 'medium', 'size_percent': 50},
        {'name': 'Budget', 'price_sensitivity': 'high', 'size_percent': 20}
    ]
    
    # Define competitors
    competitor_profiles = [
        {'name': 'Competitor A', 'aggressiveness': 'high', 'market_share_percent': 25, 'response_speed_days': 14},
        {'name': 'Competitor B', 'aggressiveness': 'medium', 'market_share_percent': 20, 'response_speed_days': 30}
    ]
    
    # Generate comprehensive impact report
    report = agent.generate_comprehensive_impact_report(
        pricing_changes=pricing_changes,
        customer_segments=customer_segments,
        competitor_profiles=competitor_profiles
    )
    
    print("Impact Analysis Summary:")
    print(f"Expected Revenue Change: ${report['key_metrics']['expected_revenue_change']}")
    print(f"Risk Level: {report['key_metrics']['risk_level']}")
    print(f"Success Probability: {report['key_metrics']['success_probability']:.2%}")
    
    # Save report
    filename = agent.save_simulation_report(report)
    print(f"Full report saved to: {filename}")