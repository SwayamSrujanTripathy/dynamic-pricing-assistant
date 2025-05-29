"""
Data Models for Dynamic Pricing Assistant
Pydantic models for type validation and data structure
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum


class ProductCategory(str, Enum):
    """Enum for supported product categories."""
    ELECTRONICS = "electronics"
    SMARTPHONES = "smartphones"
    LAPTOPS = "laptops"
    AUDIO = "audio"
    SMART_HOME = "smart_home"
    GAMING = "gaming"


class PricingStrategy(str, Enum):
    """Enum for pricing strategies."""
    PREMIUM = "premium"
    COMPETITIVE = "competitive"
    PENETRATION = "penetration"
    VALUE_BASED = "value_based"


class RiskLevel(str, Enum):
    """Enum for risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProductInput(BaseModel):
    """Input model for product pricing requests."""
    product_name: str = Field(..., min_length=1, max_length=200, description="Name of the product")
    specifications: Optional[str] = Field(default="", max_length=500, description="Product specifications")
    category: ProductCategory = Field(default=ProductCategory.ELECTRONICS, description="Product category")
    brand: Optional[str] = Field(default=None, max_length=50, description="Product brand")
    model: Optional[str] = Field(default=None, max_length=100, description="Product model")
    
    @field_validator('product_name')
    @classmethod
    def validate_product_name(cls, v):
        if not v.strip():
            raise ValueError('Product name cannot be empty')
        return v.strip()
    
    @field_validator('specifications')
    @classmethod
    def validate_specifications(cls, v):
        return v.strip() if v else ""


class PricingSource(BaseModel):
    """Model for competitor pricing data from a single source."""
    website_name: str = Field(..., description="Name of the e-commerce website")
    product_name: str = Field(..., description="Product name as found on the website")
    price: float = Field(..., gt=0, description="Product price")
    currency: str = Field(default="USD", description="Price currency")
    url: Optional[str] = Field(default=None, description="Product URL")
    availability: str = Field(default="Unknown", description="Stock availability status")
    last_updated: datetime = Field(default_factory=datetime.now, description="When the price was scraped")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CompetitorData(BaseModel):
    """Model for all competitor pricing data."""
    product_input: ProductInput
    sources: List[PricingSource] = Field(default_factory=list, description="List of pricing sources")
    scraped_at: datetime = Field(default_factory=datetime.now, description="When scraping was completed")
    total_sources: int = Field(default=0, description="Number of sources found")
    
    @field_validator('sources')
    @classmethod
    def validate_sources(cls, v):
        return v[:3]  # Limit to 3 sources as specified
    
    def get_price_range(self) -> Dict[str, float]:
        """Get min, max, and average prices from sources."""
        if not self.sources:
            return {"min": 0, "max": 0, "average": 0}
        
        prices = [source.price for source in self.sources]
        return {
            "min": min(prices),
            "max": max(prices),
            "average": sum(prices) / len(prices)
        }


class OptimizationStrategy(BaseModel):
    """Model for price optimization strategy."""
    suggested_price: float = Field(..., gt=0, description="Recommended price")
    strategy_type: PricingStrategy = Field(..., description="Type of pricing strategy")
    reasoning: str = Field(..., description="Rationale for the pricing decision")
    profit_margin_estimate: Optional[float] = Field(default=None, description="Estimated profit margin percentage")
    competitive_advantage: str = Field(default="", description="How this price provides competitive advantage")
    market_position: str = Field(..., description="Expected market position (Premium/Mid-range/Budget)")
    
    class Config:
        use_enum_values = True


class ImpactSimulation(BaseModel):
    """Model for market impact simulation results."""
    revenue_change: str = Field(..., description="Expected revenue change percentage")
    market_position: str = Field(..., description="Projected market position")
    risk_level: RiskLevel = Field(..., description="Overall risk assessment")
    demand_change: str = Field(default="", description="Expected demand change")
    competitive_response: str = Field(default="", description="Likely competitor reactions")
    roi_timeline: str = Field(default="", description="Expected ROI timeline")
    primary_risks: List[str] = Field(default_factory=list, description="Top identified risks")
    mitigation_strategies: List[str] = Field(default_factory=list, description="Risk mitigation recommendations")
    kpi_recommendations: List[str] = Field(default_factory=list, description="Key metrics to monitor")
    
    class Config:
        use_enum_values = True


class PricingResult(BaseModel):
    """Complete pricing analysis result."""
    success: bool = Field(..., description="Whether the analysis was successful")
    product_input: Optional[ProductInput] = Field(default=None, description="Original product input")
    competitor_data: Optional[CompetitorData] = Field(default=None, description="Scraped competitor data")
    optimization_strategy: Optional[OptimizationStrategy] = Field(default=None, description="Pricing strategy")
    impact_simulation: Optional[ImpactSimulation] = Field(default=None, description="Market impact analysis")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was completed")
    processing_time: Optional[float] = Field(default=None, description="Processing time in seconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentResponse(BaseModel):
    """Model for individual agent responses."""
    agent_name: str = Field(..., description="Name of the agent")
    task_completed: bool = Field(..., description="Whether the task was completed successfully")
    output: str = Field(..., description="Agent's output/response")
    execution_time: Optional[float] = Field(default=None, description="Task execution time")
    error_message: Optional[str] = Field(default=None, description="Error message if task failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="When task was completed")


class CrewExecution(BaseModel):
    """Model for complete crew execution results."""
    execution_id: str = Field(..., description="Unique execution identifier")
    product_input: ProductInput = Field(..., description="Input product data")
    agent_responses: List[AgentResponse] = Field(default_factory=list, description="Individual agent responses")
    final_result: Optional[PricingResult] = Field(default=None, description="Final pricing analysis result")
    total_execution_time: Optional[float] = Field(default=None, description="Total execution time")
    started_at: datetime = Field(default_factory=datetime.now, description="Execution start time")
    completed_at: Optional[datetime] = Field(default=None, description="Execution completion time")