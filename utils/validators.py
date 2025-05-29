import re
from typing import List, Dict, Any, Optional, Tuple
from pydantic import ValidationError
import logging
from models.data_models import ProductInput, PriceRange

logger = logging.getLogger(__name__)

class InputValidator:
    """Validation utilities for user inputs and system data"""
    
    # Electronics categories and their common specifications
    ELECTRONICS_CATEGORIES = {
        'smartphone': ['storage', 'ram', 'camera', 'battery', 'display', 'processor'],
        'laptop': ['ram', 'storage', 'processor', 'graphics', 'display', 'battery'],
        'tablet': ['storage', 'ram', 'display', 'battery', 'camera'],
        'headphones': ['type', 'wireless', 'noise_cancellation', 'battery'],
        'smartwatch': ['display', 'battery', 'sensors', 'compatibility'],
        'camera': ['megapixels', 'lens', 'video', 'storage', 'battery'],
        'tv': ['size', 'resolution', 'smart', 'hdr', 'refresh_rate'],
        'gaming_console': ['storage', 'performance', 'games', 'controllers'],
        'speaker': ['wireless', 'battery', 'water_resistance', 'power'],
        'monitor': ['size', 'resolution', 'refresh_rate', 'panel_type']
    }
    
    # Common electronics brands
    ELECTRONICS_BRANDS = [
        'apple', 'samsung', 'google', 'oneplus', 'xiaomi', 'huawei', 'sony',
        'lg', 'dell', 'hp', 'lenovo', 'asus', 'acer', 'msi', 'razer',
        'nintendo', 'xbox', 'playstation', 'bose', 'sennheiser', 'jbl',
        'beats', 'airpods', 'canon', 'nikon', 'gopro', 'fitbit', 'garmin'
    ]
    
    def __init__(self):
        self.valid_currencies = ['USD', 'INR', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD']
        self.valid_websites = [
            'amazon.com', 'flipkart.com', 'myntra.com', 'snapdeal.com',
            'ebay.com', 'bestbuy.com', 'walmart.com', 'target.com',
            'newegg.com', 'croma.com', 'reliance.com'
        ]
    
    def validate_product_input(self, product_name: str, specifications: Optional[Dict] = None) -> Tuple[bool, str, Optional[ProductInput]]:
        """Validate product input and return validation result"""
        try:
            # Basic validation
            if not product_name or not isinstance(product_name, str):
                return False, "Product name is required and must be a string", None
            
            product_name = product_name.strip()
            if len(product_name) < 2:
                return False, "Product name must be at least 2 characters long", None
            
            if len(product_name) > 200:
                return False, "Product name is too long (max 200 characters)", None
            
            # Check if it's an electronics product
            is_electronics, category = self.is_electronics_product(product_name)
            if not is_electronics:
                return False, "Only electronics products are supported currently", None
            
            # Validate specifications if provided
            if specifications:
                is_spec_valid, spec_error = self.validate_specifications(specifications, category)
                if not is_spec_valid:
                    return False, f"Invalid specifications: {spec_error}", None
            
            # Create ProductInput object
            product_input = ProductInput(
                name=product_name,
                category=category,
                specifications=specifications or {},
                brand=self.extract_brand(product_name)
            )
            
            return True, "Valid product input", product_input
            
        except Exception as e:
            logger.error(f"Error validating product input: {str(e)}")
            return False, f"Validation error: {str(e)}", None
    
    def is_electronics_product(self, product_name: str) -> Tuple[bool, Optional[str]]:
        """Check if product is an electronics item and determine category"""
        product_lower = product_name.lower()
        
        # Check for direct category matches
        for category, specs in self.ELECTRONICS_CATEGORIES.items():
            if category in product_lower:
                return True, category
        
        # Check for common electronics keywords
        electronics_keywords = [
            'phone', 'mobile', 'iphone', 'android', 'smartphone',
            'laptop', 'computer', 'pc', 'macbook', 'notebook',
            'tablet', 'ipad', 'kindle',
            'headphones', 'earphones', 'earbuds', 'airpods',
            'watch', 'smartwatch', 'fitness tracker',
            'camera', 'dslr', 'mirrorless', 'gopro',
            'tv', 'television', 'smart tv', 'led', 'oled',
            'console', 'xbox', 'playstation', 'nintendo',
            'speaker', 'bluetooth speaker', 'smart speaker',
            'monitor', 'display', 'screen'
        ]
        
        for keyword in electronics_keywords:
            if keyword in product_lower:
                # Map keywords to categories
                if any(k in keyword for k in ['phone', 'mobile', 'iphone', 'android']):
                    return True, 'smartphone'
                elif any(k in keyword for k in ['laptop', 'computer', 'pc', 'macbook', 'notebook']):
                    return True, 'laptop'
                elif any(k in keyword for k in ['tablet', 'ipad', 'kindle']):
                    return True, 'tablet'
                elif any(k in keyword for k in ['headphones', 'earphones', 'earbuds', 'airpods']):
                    return True, 'headphones'
                elif any(k in keyword for k in ['watch', 'smartwatch', 'fitness tracker']):
                    return True, 'smartwatch'
                elif any(k in keyword for k in ['camera', 'dslr', 'mirrorless', 'gopro']):
                    return True, 'camera'
                elif any(k in keyword for k in ['tv', 'television']):
                    return True, 'tv'
                elif any(k in keyword for k in ['console', 'xbox', 'playstation', 'nintendo']):
                    return True, 'gaming_console'
                elif any(k in keyword for k in ['speaker']):
                    return True, 'speaker'
                elif any(k in keyword for k in ['monitor', 'display']):
                    return True, 'monitor'
                else:
                    return True, 'smartphone'  # Default category
        
        # Check for brand names
        for brand in self.ELECTRONICS_BRANDS:
            if brand in product_lower:
                return True, self.get_default_category_for_brand(brand)
        
        return False, None
    
    def get_default_category_for_brand(self, brand: str) -> str:
        """Get default category for known brands"""
        brand_categories = {
            'apple': 'smartphone',
            'samsung': 'smartphone',
            'google': 'smartphone',
            'oneplus': 'smartphone',
            'xiaomi': 'smartphone',
            'huawei': 'smartphone',
            'dell': 'laptop',
            'hp': 'laptop',
            'lenovo': 'laptop',
            'asus': 'laptop',
            'acer': 'laptop',
            'msi': 'laptop',
            'sony': 'headphones',
            'bose': 'headphones',
            'sennheiser': 'headphones',
            'jbl': 'speaker',
            'beats': 'headphones',
            'canon': 'camera',
            'nikon': 'camera',
            'gopro': 'camera',
            'fitbit': 'smartwatch',
            'garmin': 'smartwatch',
            'lg': 'tv',
            'nintendo': 'gaming_console'
        }
        return brand_categories.get(brand.lower(), 'smartphone')
    
    def extract_brand(self, product_name: str) -> Optional[str]:
        """Extract brand from product name"""
        product_lower = product_name.lower()
        
        for brand in self.ELECTRONICS_BRANDS:
            if brand in product_lower:
                return brand.title()
        
        return None
    
    def validate_specifications(self, specifications: Dict, category: str) -> Tuple[bool, str]:
        """Validate product specifications"""
        if not isinstance(specifications, dict):
            return False, "Specifications must be a dictionary"
        
        # Get expected specs for category
        expected_specs = self.ELECTRONICS_CATEGORIES.get(category, [])
        
        # Validate each specification
        for key, value in specifications.items():
            if not isinstance(key, str):
                return False, f"Specification key must be string: {key}"
            
            if not value:  # Allow empty values but not None
                continue
                
            # Validate specific specification types
            validation_result = self.validate_specific_spec(key, value, category)
            if not validation_result[0]:
                return False, validation_result[1]
        
        return True, "Valid specifications"
    
    def validate_specific_spec(self, spec_key: str, spec_value: Any, category: str) -> Tuple[bool, str]:
        """Validate specific specification based on type"""
        spec_key_lower = spec_key.lower()
        
        try:
            # Storage validation
            if 'storage' in spec_key_lower or 'memory' in spec_key_lower:
                if isinstance(spec_value, str):
                    if not re.match(r'^\d+\s*(gb|tb|mb)$', spec_value.lower().strip()):
                        return False, f"Invalid storage format: {spec_value}. Use format like '64GB' or '1TB'"
            
            # RAM validation
            elif 'ram' in spec_key_lower:
                if isinstance(spec_value, str):
                    if not re.match(r'^\d+\s*(gb|mb)$', spec_value.lower().strip()):
                        return False, f"Invalid RAM format: {spec_value}. Use format like '8GB'"
            
            # Display size validation
            elif 'display' in spec_key_lower or 'size' in spec_key_lower:
                if isinstance(spec_value, str):
                    if not re.match(r'^\d+(\.\d+)?\s*(inch|"|cm)$', spec_value.lower().strip()):
                        return False, f"Invalid display size format: {spec_value}. Use format like '6.1 inch'"
            
            # Camera validation
            elif 'camera' in spec_key_lower or 'megapixel' in spec_key_lower:
                if isinstance(spec_value, str):
                    if not re.match(r'^\d+\s*(mp|megapixel)$', spec_value.lower().strip()):
                        return False, f"Invalid camera format: {spec_value}. Use format like '12MP'"
            
            # Battery validation
            elif 'battery' in spec_key_lower:
                if isinstance(spec_value, str):
                    if not re.match(r'^\d+\s*(mah|wh)$', spec_value.lower().strip()):
                        return False, f"Invalid battery format: {spec_value}. Use format like '4000mAh'"
            
            return True, "Valid specification"
            
        except Exception as e:
            return False, f"Error validating {spec_key}: {str(e)}"
    
    def validate_price_range(self, min_price: Optional[float], max_price: Optional[float]) -> Tuple[bool, str]:
        """Validate price range"""
        if min_price is not None:
            if not isinstance(min_price, (int, float)) or min_price < 0:
                return False, "Minimum price must be a positive number"
        
        if max_price is not None:
            if not isinstance(max_price, (int, float)) or max_price < 0:
                return False, "Maximum price must be a positive number"
        
        if min_price is not None and max_price is not None:
            if min_price >= max_price:
                return False, "Minimum price must be less than maximum price"
        
        return True, "Valid price range"
    
    def validate_website_url(self, url: str) -> Tuple[bool, str]:
        """Validate website URL"""
        if not url or not isinstance(url, str):
            return False, "URL is required and must be a string"
        
        url = url.strip().lower()
        
        # Basic URL pattern validation
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url):
            return False, "Invalid URL format"
        
        # Check if it's a supported website
        is_supported = any(website in url for website in self.valid_websites)
        if not is_supported:
            return False, f"Website not supported. Supported websites: {', '.join(self.valid_websites)}"
        
        return True, "Valid URL"
    
    def validate_currency(self, currency: str) -> bool:
        """Validate currency code"""
        return currency.upper() in self.valid_currencies
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        if not isinstance(text, str):
            return str(text)
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\';\\]', '', text)
        
        # Limit length
        sanitized = sanitized[:500]
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
    
    def validate_competitor_data(self, data: Dict) -> Tuple[bool, str]:
        """Validate scraped competitor data"""
        required_fields = ['website', 'product_name', 'price']
        
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
            
            if not data[field]:
                return False, f"Empty value for required field: {field}"
        
        # Validate price
        try:
            price = float(data['price'])
            if price < 0:
                return False, "Price cannot be negative"
        except (ValueError, TypeError):
            return False, "Invalid price format"
        
        # Validate currency if provided
        if 'currency' in data and data['currency']:
            if not self.validate_currency(data['currency']):
                return False, f"Invalid currency: {data['currency']}"
        
        return True, "Valid competitor data"