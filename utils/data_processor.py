import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import re
from datetime import datetime
import json
import logging
from models.data_models import PriceData, CompetitorData, PriceOptimizationResult

logger = logging.getLogger(__name__)

class DataProcessor:
    """Utility class for processing scraped data and preparing it for analysis"""
    
    def __init__(self):
        self.price_patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1,234.56
            r'₹(\d+(?:,\d{3})*(?:\.\d{2})?)',   # ₹1,234.56
            r'(\d+(?:,\d{3})*(?:\.\d{2})?) *(?:USD|INR|Rs\.?)',  # 1234.56 USD
            r'Price[:\s]*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # Price: 1234.56
        ]
    
    def clean_price_text(self, price_text: str) -> Optional[float]:
        """Extract and clean price from text"""
        if not price_text:
            return None
            
        price_text = str(price_text).strip()
        
        # Try different price patterns
        for pattern in self.price_patterns:
            match = re.search(pattern, price_text, re.IGNORECASE)
            if match:
                price_str = match.group(1)
                # Remove commas and convert to float
                try:
                    price = float(price_str.replace(',', ''))
                    return price
                except ValueError:
                    continue
        
        # Fallback: try to extract any number that looks like a price
        numbers = re.findall(r'\d+(?:\.\d{2})?', price_text)
        if numbers:
            try:
                # Return the largest number (likely the price)
                prices = [float(num) for num in numbers]
                return max(prices) if prices else None
            except ValueError:
                pass
        
        return None
    
    def normalize_product_name(self, product_name: str) -> str:
        """Normalize product name for better matching"""
        if not product_name:
            return ""
        
        # Convert to lowercase and remove extra spaces
        normalized = re.sub(r'\s+', ' ', product_name.lower().strip())
        
        # Remove common prefixes/suffixes that might cause confusion
        remove_words = ['new', 'original', 'genuine', 'authentic', 'latest']
        words = normalized.split()
        filtered_words = [word for word in words if word not in remove_words]
        
        return ' '.join(filtered_words)
    
    def process_scraped_data(self, raw_data: List[Dict[str, Any]]) -> List[CompetitorData]:
        """Process raw scraped data into structured format"""
        processed_data = []
        
        for item in raw_data:
            try:
                # Extract and clean price
                price = self.clean_price_text(item.get('price', ''))
                if price is None:
                    logger.warning(f"Could not extract price from: {item.get('price', 'N/A')}")
                    continue
                
                # Create CompetitorData object
                competitor_data = CompetitorData(
                    website=item.get('website', 'Unknown'),
                    product_name=self.normalize_product_name(item.get('product_name', '')),
                    price=price,
                    currency=item.get('currency', 'USD'),
                    availability=item.get('availability', True),
                    rating=self.clean_rating(item.get('rating')),
                    reviews_count=self.clean_number(item.get('reviews_count')),
                    specifications=item.get('specifications', {}),
                    url=item.get('url', ''),
                    scraped_at=datetime.now()
                )
                
                processed_data.append(competitor_data)
                
            except Exception as e:
                logger.error(f"Error processing item {item}: {str(e)}")
                continue
        
        return processed_data
    
    def clean_rating(self, rating_text: Any) -> Optional[float]:
        """Extract rating from text"""
        if not rating_text:
            return None
        
        rating_str = str(rating_text)
        # Look for patterns like "4.5", "4.5/5", "4.5 out of 5"
        match = re.search(r'(\d+\.?\d*)', rating_str)
        if match:
            try:
                rating = float(match.group(1))
                # Normalize to 5-point scale if needed
                if rating > 5:
                    rating = rating / 2  # Assume 10-point scale
                return min(rating, 5.0)
            except ValueError:
                pass
        
        return None
    
    def clean_number(self, number_text: Any) -> Optional[int]:
        """Extract number from text (for reviews count, etc.)"""
        if not number_text:
            return None
        
        number_str = str(number_text)
        # Remove commas and extract number
        match = re.search(r'(\d+(?:,\d{3})*)', number_str)
        if match:
            try:
                return int(match.group(1).replace(',', ''))
            except ValueError:
                pass
        
        return None
    
    def calculate_price_statistics(self, competitor_data: List[CompetitorData]) -> Dict[str, float]:
        """Calculate price statistics from competitor data"""
        if not competitor_data:
            return {}
        
        prices = [data.price for data in competitor_data if data.price > 0]
        
        if not prices:
            return {}
        
        return {
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_price': np.mean(prices),
            'median_price': np.median(prices),
            'std_price': np.std(prices),
            'price_range': max(prices) - min(prices),
            'count': len(prices)
        }
    
    def filter_relevant_competitors(self, competitor_data: List[CompetitorData], 
                                  target_product: str, similarity_threshold: float = 0.7) -> List[CompetitorData]:
        """Filter competitors based on product similarity"""
        if not competitor_data:
            return []
        
        target_normalized = self.normalize_product_name(target_product)
        target_words = set(target_normalized.split())
        
        relevant_competitors = []
        
        for competitor in competitor_data:
            competitor_words = set(competitor.product_name.split())
            
            # Calculate Jaccard similarity
            intersection = len(target_words & competitor_words)
            union = len(target_words | competitor_words)
            
            similarity = intersection / union if union > 0 else 0
            
            if similarity >= similarity_threshold:
                relevant_competitors.append(competitor)
        
        return relevant_competitors
    
    def prepare_optimization_data(self, competitor_data: List[CompetitorData], 
                                current_price: Optional[float] = None) -> Dict[str, Any]:
        """Prepare data for price optimization"""
        if not competitor_data:
            return {}
        
        price_stats = self.calculate_price_statistics(competitor_data)
        
        # Calculate market position if current price is provided
        market_position = None
        if current_price and price_stats:
            if current_price < price_stats['min_price']:
                market_position = 'below_market'
            elif current_price > price_stats['max_price']:
                market_position = 'above_market'
            else:
                market_position = 'within_market'
        
        # Group by website for analysis
        website_data = {}
        for competitor in competitor_data:
            website = competitor.website
            if website not in website_data:
                website_data[website] = []
            website_data[website].append({
                'price': competitor.price,
                'rating': competitor.rating,
                'reviews_count': competitor.reviews_count,
                'availability': competitor.availability
            })
        
        return {
            'price_statistics': price_stats,
            'market_position': market_position,
            'competitor_count': len(competitor_data),
            'website_breakdown': website_data,
            'avg_rating': np.mean([c.rating for c in competitor_data if c.rating]),
            'total_reviews': sum([c.reviews_count for c in competitor_data if c.reviews_count])
        }
    
    def format_results_for_display(self, optimization_result: PriceOptimizationResult) -> str:
        """Format optimization results for display"""
        result_text = f"""
PRICE OPTIMIZATION RESULTS
==========================

Recommended Price: ${optimization_result.recommended_price:.2f}
Strategy: {optimization_result.strategy}
Confidence: {optimization_result.confidence:.1%}

Market Analysis:
- Minimum Market Price: ${optimization_result.market_analysis['min_price']:.2f}
- Maximum Market Price: ${optimization_result.market_analysis['max_price']:.2f}
- Average Market Price: ${optimization_result.market_analysis['avg_price']:.2f}

Expected Impact:
- Profit Margin: {optimization_result.expected_impact.get('profit_margin', 'N/A')}
- Market Share: {optimization_result.expected_impact.get('market_share', 'N/A')}
- Revenue Change: {optimization_result.expected_impact.get('revenue_change', 'N/A')}

Reasoning: {optimization_result.reasoning}
"""
        return result_text.strip()
    
    def export_to_dataframe(self, competitor_data: List[CompetitorData]) -> pd.DataFrame:
        """Export competitor data to pandas DataFrame"""
        if not competitor_data:
            return pd.DataFrame()
        
        data_dict = []
        for competitor in competitor_data:
            data_dict.append({
                'website': competitor.website,
                'product_name': competitor.product_name,
                'price': competitor.price,
                'currency': competitor.currency,
                'availability': competitor.availability,
                'rating': competitor.rating,
                'reviews_count': competitor.reviews_count,
                'url': competitor.url,
                'scraped_at': competitor.scraped_at
            })
        
        return pd.DataFrame(data_dict)
    
    def save_processed_data(self, data: List[CompetitorData], filename: str):
        """Save processed data to JSON file"""
        try:
            serializable_data = []
            for item in data:
                serializable_data.append(item.dict())
            
            with open(filename, 'w') as f:
                json.dump(serializable_data, f, indent=2, default=str)
                
            logger.info(f"Data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")