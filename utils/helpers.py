def clean_price(price_str: str) -> float:
    """Clean price string and convert to float."""
    try:
        # Remove currency symbols and commas
        cleaned = price_str.replace("₹", "").replace(",", "").strip()
        return float(cleaned)
    except:
        return 0.0