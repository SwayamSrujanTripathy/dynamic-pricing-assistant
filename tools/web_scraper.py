import requests
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus, urljoin
import logging
from models.data_models import PricingSource, ProductCategory
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraperTool:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver with appropriate options"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--user-agent={settings.USER_AGENT}')
        
        driver = webdriver.Chrome(
            ChromeDriverManager().install(),
            options=options
        )
        return driver
    
    def _extract_price(self, text: str) -> Optional[float]:
        """Extract price from text using regex patterns"""
        # Common price patterns for Indian e-commerce
        patterns = [
            r'₹\s*([0-9,]+(?:\.[0-9]{2})?)',  # ₹1,234.56
            r'INR\s*([0-9,]+(?:\.[0-9]{2})?)',  # INR 1,234.56
            r'Rs\.?\s*([0-9,]+(?:\.[0-9]{2})?)',  # Rs. 1,234.56
            r'\$\s*([0-9,]+(?:\.[0-9]{2})?)',  # $1,234.56
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        return None
    
    def _extract_rating(self, text: str) -> Optional[float]:
        """Extract rating from text"""
        patterns = [
            r'([0-4](?:\.[0-9])?)\s*out\s*of\s*5',
            r'([0-4](?:\.[0-9])?)\s*/\s*5',
            r'★\s*([0-4](?:\.[0-9])?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return None
    
    def scrape_amazon(self, product_name: str, specifications: str = "") -> Optional[PricingSource]:
        """Scrape product data from Amazon"""
        try:
            search_query = f"{product_name} {specifications}".strip()
            search_url = f"https://www.amazon.in/s?k={quote_plus(search_query)}"
            
            driver = self._setup_driver()
            driver.get(search_url)
            
            # Wait for search results to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-component-type="s-search-result"]'))
            )
            
            # Get first relevant product
            products = driver.find_elements(By.CSS_SELECTOR, '[data-component-type="s-search-result"]')
            
            for product in products[:3]:  # Check first 3 results
                try:
                    # Extract price
                    price_elem = product.find_element(By.CSS_SELECTOR, '.a-price-whole, .a-offscreen')
                    price_text = price_elem.text
                    price = self._extract_price(price_text)
                    
                    if not price:
                        continue
                    
                    # Extract product link
                    link_elem = product.find_element(By.CSS_SELECTOR, 'h2 a')
                    product_url = urljoin("https://www.amazon.in", link_elem.get_attribute('href'))
                    
                    # Extract rating if available
                    rating = None
                    try:
                        rating_elem = product.find_element(By.CSS_SELECTOR, '.a-icon-alt')
                        rating = self._extract_rating(rating_elem.get_attribute('textContent'))
                    except:
                        pass
                    
                    driver.quit()
                    
                    return PricingSource(
                        website="amazon.in",
                        url=product_url,
                        price=price,
                        currency="INR",
                        availability=True,
                        rating=rating
                    )
                    
                except Exception as e:
                    logger.warning(f"Error extracting Amazon product data: {e}")
                    continue
            
            driver.quit()
            
        except Exception as e:
            logger.error(f"Error scraping Amazon: {e}")
            
        return None
    
    def scrape_flipkart(self, product_name: str, specifications: str = "") -> Optional[PricingSource]:
        """Scrape product data from Flipkart"""
        try:
            search_query = f"{product_name} {specifications}".strip()
            search_url = f"https://www.flipkart.com/search?q={quote_plus(search_query)}"
            
            driver = self._setup_driver()
            driver.get(search_url)
            
            # Wait for search results
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-tkid], ._1AtVbE'))
            )
            
            # Get product containers
            products = driver.find_elements(By.CSS_SELECTOR, '[data-tkid], ._1AtVbE')
            
            for product in products[:3]:
                try:
                    # Extract price
                    price_elem = product.find_element(By.CSS_SELECTOR, '._30jeq3, ._1_WHN1')
                    price = self._extract_price(price_elem.text)
                    
                    if not price:
                        continue
                    
                    # Extract product link
                    link_elem = product.find_element(By.CSS_SELECTOR, 'a')
                    product_url = urljoin("https://www.flipkart.com", link_elem.get_attribute('href'))
                    
                    # Extract rating
                    rating = None
                    try:
                        rating_elem = product.find_element(By.CSS_SELECTOR, '._3LWZlK')
                        rating = float(rating_elem.text)
                    except:
                        pass
                    
                    driver.quit()
                    
                    return PricingSource(
                        website="flipkart.com",
                        url=product_url,
                        price=price,
                        currency="INR",
                        availability=True,
                        rating=rating
                    )
                    
                except Exception as e:
                    logger.warning(f"Error extracting Flipkart product data: {e}")
                    continue
            
            driver.quit()
            
        except Exception as e:
            logger.error(f"Error scraping Flipkart: {e}")
            
        return None
    
    def scrape_myntra(self, product_name: str, specifications: str = "") -> Optional[PricingSource]:
        """Scrape product data from Myntra (for electronics available there)"""
        try:
            search_query = f"{product_name} {specifications}".strip()
            search_url = f"https://www.myntra.com/{quote_plus(search_query)}"
            
            # Use requests for Myntra as it's more stable
            response = self.session.get(search_url, timeout=settings.REQUEST_TIMEOUT)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for product listings
            products = soup.find_all('li', class_='product-base')
            
            for product in products[:3]:
                try:
                    # Extract price
                    price_elem = product.find('span', class_='product-discountedPrice')
                    if not price_elem:
                        price_elem = product.find('span', class_='product-strike')
                    
                    if price_elem:
                        price = self._extract_price(price_elem.text)
                        if not price:
                            continue
                        
                        # Extract product link
                        link_elem = product.find('a')
                        if link_elem:
                            product_url = urljoin("https://www.myntra.com", link_elem.get('href'))
                            
                            return PricingSource(
                                website="myntra.com",
                                url=product_url,
                                price=price,
                                currency="INR",
                                availability=True
                            )
                
                except Exception as e:
                    logger.warning(f"Error extracting Myntra product data: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping Myntra: {e}")
            
        return None
    
    def scrape_multiple_sources(self, product_name: str, specifications: str = "") -> List[PricingSource]:
        """Scrape product data from multiple sources"""
        sources = []
        scrapers = [
            ("Amazon", self.scrape_amazon),
            ("Flipkart", self.scrape_flipkart),
            ("Myntra", self.scrape_myntra)
        ]
        
        for site_name, scraper_func in scrapers:
            try:
                logger.info(f"Scraping {site_name} for {product_name}")
                result = scraper_func(product_name, specifications)
                
                if result:
                    sources.append(result)
                    logger.info(f"Successfully scraped {site_name}: ₹{result.price}")
                else:
                    logger.warning(f"No results from {site_name}")
                
                # Rate limiting
                time.sleep(settings.SCRAPING_DELAY)
                
            except Exception as e:
                logger.error(f"Error scraping {site_name}: {e}")
                continue
        
        return sources[:settings.MAX_WEBSITES]
    
    def validate_product_category(self, product_name: str) -> Tuple[bool, Optional[ProductCategory]]:
        """Validate if product belongs to supported electronic categories"""
        product_lower = product_name.lower()
        
        category_keywords = {
            ProductCategory.SMARTPHONES: ['phone', 'smartphone', 'mobile', 'iphone', 'android'],
            ProductCategory.LAPTOPS: ['laptop', 'notebook', 'macbook', 'computer', 'pc'],
            ProductCategory.TABLETS: ['tablet', 'ipad', 'tab'],
            ProductCategory.SMARTWATCHES: ['watch', 'smartwatch', 'wearable'],
            ProductCategory.HEADPHONES: ['headphone', 'earphone', 'earbud', 'airpods'],
            ProductCategory.CAMERAS: ['camera', 'dslr', 'mirrorless', 'camcorder'],
            ProductCategory.GAMING_CONSOLES: ['console', 'playstation', 'xbox', 'nintendo', 'gaming'],
            ProductCategory.SPEAKERS: ['speaker', 'bluetooth', 'soundbar', 'audio'],
            ProductCategory.MONITORS: ['monitor', 'display', 'screen'],
            ProductCategory.TELEVISIONS: ['tv', 'television', 'smart tv', 'led', 'oled']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in product_lower for keyword in keywords):
                return True, category
        
        return False, None