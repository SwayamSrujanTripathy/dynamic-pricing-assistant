"""
Competitor Scraping Agent using Gemini 2.0 Flash
Scrapes and analyzes competitor pricing data
"""

import requests
import pandas as pd
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import google.generativeai as genai
from urllib.parse import urljoin, urlparse
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompetitorScrapingAgent:
    def __init__(self, gemini_api_key: str):
        """
        Initialize the competitor scraping agent with Gemini 2.0 Flash
        
        Args:
            gemini_api_key: Google Gemini API key
        """
        self.gemini_api_key = gemini_api_key
        genai.configure(api_key=gemini_api_key)
        
        # Initialize Gemini model (using flash for CPU efficiency)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.scraped_data = []
        
    def scrape_competitor_page(self, url: str, product_keywords: List[str]) -> Dict:
        """
        Scrape a competitor's page for product pricing information
        
        Args:
            url: Competitor website URL
            product_keywords: Keywords to identify relevant products
            
        Returns:
            Dictionary containing scraped pricing data
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text content
            page_text = soup.get_text()
            
            # Use Gemini to analyze and extract pricing data
            pricing_data = self._analyze_pricing_with_gemini(page_text, product_keywords, url)
            
            return {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'pricing_data': pricing_data,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'error': str(e),
                'status': 'failed'
            }
    
    def _analyze_pricing_with_gemini(self, page_content: str, keywords: List[str], url: str) -> List[Dict]:
        """
        Use Gemini to analyze page content and extract pricing information
        
        Args:
            page_content: Raw text content from the page
            keywords: Product keywords to look for
            url: Source URL for context
            
        Returns:
            List of extracted product pricing data
        """
        # Truncate content if too long (Gemini has token limits)
        if len(page_content) > 8000:
            page_content = page_content[:8000] + "..."
        
        prompt = f"""
        Analyze the following webpage content and extract product pricing information.
        
        Keywords to look for: {', '.join(keywords)}
        Source URL: {url}
        
        Webpage Content:
        {page_content}
        
        Please extract and return pricing information in the following JSON format:
        {{
            "products": [
                {{
                    "name": "product name",
                    "price": "numeric price value",
                    "currency": "currency symbol/code",
                    "original_price": "original price if discounted",
                    "discount_percent": "discount percentage if any",
                    "availability": "in stock/out of stock",
                    "description": "brief product description"
                }}
            ]
        }}
        
        Only include products that match the given keywords. If no pricing information is found, return an empty products array.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                pricing_data = json.loads(json_match.group())
                return pricing_data.get('products', [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error analyzing with Gemini: {str(e)}")
            return []
    
    def scrape_multiple_competitors(self, competitor_urls: List[str], product_keywords: List[str]) -> pd.DataFrame:
        """
        Scrape multiple competitor websites
        
        Args:
            competitor_urls: List of competitor URLs to scrape
            product_keywords: Keywords to identify relevant products
            
        Returns:
            DataFrame containing all scraped pricing data
        """
        all_data = []
        
        for url in competitor_urls:
            logger.info(f"Scraping {url}...")
            
            result = self.scrape_competitor_page(url, product_keywords)
            
            if result['status'] == 'success':
                for product in result['pricing_data']:
                    product_data = {
                        'competitor_url': url,
                        'competitor_name': urlparse(url).netloc,
                        'scraped_at': result['scraped_at'],
                        **product
                    }
                    all_data.append(product_data)
            
            # Add delay to be respectful to servers
            time.sleep(2)
        
        df = pd.DataFrame(all_data)
        self.scraped_data = all_data
        
        return df
    
    def analyze_pricing_trends(self, df: pd.DataFrame) -> Dict:
        """
        Analyze pricing trends from scraped data using Gemini
        
        Args:
            df: DataFrame containing scraped pricing data
            
        Returns:
            Dictionary containing pricing analysis
        """
        if df.empty:
            return {"error": "No data to analyze"}
        
        # Prepare data summary for Gemini analysis
        data_summary = df.groupby('competitor_name').agg({
            'price': ['mean', 'min', 'max', 'count'],
            'name': 'count'
        }).to_string()
        
        prompt = f"""
        Analyze the following competitor pricing data and provide insights:
        
        Pricing Data Summary:
        {data_summary}
        
        Raw data sample:
        {df.head(10).to_string()}
        
        Please provide analysis in the following areas:
        1. Average pricing by competitor
        2. Price range analysis
        3. Most competitive pricing
        4. Pricing patterns and trends
        5. Recommendations for pricing strategy
        
        Format your response as structured insights that can be used for business decisions.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            return {
                'analysis': response.text,
                'data_summary': {
                    'total_products': len(df),
                    'competitors_analyzed': df['competitor_name'].nunique(),
                    'average_price': df['price'].mean() if 'price' in df.columns else None,
                    'price_range': {
                        'min': df['price'].min() if 'price' in df.columns else None,
                        'max': df['price'].max() if 'price' in df.columns else None
                    }
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in pricing analysis: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def save_data(self, filename: str = None) -> str:
        """
        Save scraped data to CSV file
        
        Args:
            filename: Optional filename, defaults to timestamp-based name
            
        Returns:
            Filename of saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"competitor_data_{timestamp}.csv"
        
        df = pd.DataFrame(self.scraped_data)
        df.to_csv(filename, index=False)
        
        logger.info(f"Data saved to {filename}")
        return filename
    
    def get_summary_report(self) -> Dict:
        """
        Generate a summary report of scraping activity
        
        Returns:
            Dictionary containing summary statistics
        """
        if not self.scraped_data:
            return {"message": "No data scraped yet"}
        
        df = pd.DataFrame(self.scraped_data)
        
        return {
            'total_products_found': len(df),
            'unique_competitors': df['competitor_name'].nunique() if 'competitor_name' in df.columns else 0,
            'date_range': {
                'latest_scrape': max([item.get('scraped_at', '') for item in self.scraped_data]),
                'earliest_scrape': min([item.get('scraped_at', '') for item in self.scraped_data])
            },
            'average_products_per_competitor': len(df) / df['competitor_name'].nunique() if 'competitor_name' in df.columns and df['competitor_name'].nunique() > 0 else 0
        }

# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = CompetitorScrapingAgent("your-gemini-api-key")
    
    # Example competitor URLs and keywords
    competitor_urls = [
        "https://example-competitor1.com/products",
        "https://example-competitor2.com/pricing"
    ]
    
    product_keywords = ["laptop", "computer", "electronics"]
    
    # Scrape competitors
    df = agent.scrape_multiple_competitors(competitor_urls, product_keywords)
    print(f"Scraped {len(df)} products")
    
    # Analyze trends
    analysis = agent.analyze_pricing_trends(df)
    print("Pricing Analysis:", analysis)
    
    # Save data
    filename = agent.save_data()
    print(f"Data saved to {filename}")