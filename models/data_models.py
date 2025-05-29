from dataclasses import dataclass
from typing import Optional

@dataclass
class PricingSource:
    source: str
    url: str

@dataclass
class ProductCategory:
    name: str
    description: Optional[str] = None

@dataclass
class ProductSpecifications:
    name: str
    specs: dict
    category: Optional[ProductCategory] = None