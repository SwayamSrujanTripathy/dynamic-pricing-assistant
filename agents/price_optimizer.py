import logging
import re
import json
 
logger = logging.getLogger(__name__)
 
class PriceOptimizerAgent:
    def __init__(self):
        pass
 
    def execute(self, products: list, query: str) -> dict:
        """
        Suggest an optimal price to maximize customer influx while maintaining profitability.
       
        Args:
            products (list): List of competitor products with name, price, and platform.
            query (str): Product query (e.g., "Samsung Galaxy A54, Specifications: 8GB RAM, 256GB storage").
       
        Returns:
            dict: Suggested price and strategy.
        """
        try:
            logger.info(f"Executing PriceOptimizerAgent with {len(products)} products")
            if not products:
                logger.warning("No prices found for optimization")
                # Fallback: Assume smartphone market standard
                product_name = query.split("Specifications:")[0].replace("Product:", "").strip().lower()
                suggested_price = "₹20,000"
                strategy = f"No competitor data for {product_name}. Set ₹20,000 as a competitive price for mid-range smartphones to attract customers."
                return {"suggested_price": suggested_price, "strategy": strategy}
 
            # Extract prices
            prices = []
            for product in products:
                try:
                    price_str = product["price"].replace("₹", "").replace(",", "")
                    price = int(price_str)
                    prices.append(price)
                except (ValueError, KeyError) as e:
                    logger.error(f"Error parsing price: {e}")
                    continue
 
            if not prices:
                logger.warning("No valid prices extracted")
                suggested_price = "₹20,000"
                strategy = "No valid competitor prices. Set ₹20,000 for mid-range smartphones."
                return {"suggested_price": suggested_price, "strategy": strategy}
 
            # Calculate average price
            avg_price = sum(prices) / len(prices)
            # Estimate cost price (70% of lowest competitor price)
            cost_price = min(prices) * 0.7
            # Suggest price: 10% below average, ensure 15% margin
            target_price = avg_price * 0.9
            min_price = cost_price * 1.15  # Ensure 15% margin
 
            suggested_price = max(target_price, min_price)
            suggested_price = round(suggested_price / 100) * 100  # Round to nearest 100
            suggested_price_str = f"₹{int(suggested_price):,}"
 
            product_name = query.split("Specifications:")[0].replace("Product:", "").strip()
            strategy = (
                f"Set price for {product_name} at ₹{int(suggested_price):,} (10% below competitor average of ₹{int(avg_price):,}) "
                f"to attract more customers. Ensures at least 15% margin over estimated cost of ₹{int(cost_price):,}."
            )
 
            logger.info(f"Suggested price: {suggested_price_str}, Strategy: {strategy}")
            return {"suggested_price": suggested_price_str, "strategy": strategy}
 
        except Exception as e:
            logger.error(f"PriceOptimizerAgent error: {e}")
            return {"suggested_price": "₹0", "strategy": f"Error: {str(e)}"}