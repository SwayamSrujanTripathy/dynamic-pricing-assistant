#!/usr/bin/env python3
"""
Dynamic Pricing Assistant - Main Entry Point
A multi-agent system for analyzing competitor pricing and providing dynamic pricing strategies
for electronic devices using CrewAI framework.
"""

import os
import sys
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Using system environment variables only.")

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from crewai import Crew
try:
    from config.settings import Settings
    from crew.pricing_crew import PricingCrew
    from utils.validators import ProductValidator
    from utils.data_processor import DataProcessor
    from models.data_models import ProductInput, PricingResult
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("📋 Missing modules detected. Creating basic structure...")
    
    # Create basic fallback classes if modules don't exist
    class Settings:
        def __init__(self):
            self.gemini_api_key = os.getenv('GEMINI_API_KEY')
            self.pinecone_api_key = os.getenv('PINECONE_API_KEY')
    
    class PricingCrew:
        def __init__(self):
            print("⚠️  Using fallback PricingCrew - please implement crew/pricing_crew.py")
        
        def get_crew(self):
            print("⚠️  Crew not implemented yet")
            return None
    
    class ProductValidator:
        def validate_product_input(self, product_input):
            return True
    
    class DataProcessor:
        def format_pricing_results(self, result):
            return result
        
        def get_timestamp(self):
            from datetime import datetime
            return datetime.now().isoformat()
    
    class ProductInput:
        def __init__(self, product_name, specifications="", category="electronics"):
            self.product_name = product_name
            self.specifications = specifications
            self.category = category
    
    class PricingResult:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


class DynamicPricingAssistant:
    """
    Main application class for the Dynamic Pricing Assistant.
    Orchestrates the multi-agent workflow for competitive pricing analysis.
    """
    
    def __init__(self):
        """Initialize the Dynamic Pricing Assistant."""
        self.settings = Settings()
        self.validator = ProductValidator()
        self.data_processor = DataProcessor()
        self.pricing_crew = None
        self._initialize_crew()
    
    def _initialize_crew(self):
        """Initialize the CrewAI crew with all agents and tasks."""
        try:
            self.pricing_crew = PricingCrew()
            print("✅ Dynamic Pricing Assistant initialized successfully!")
            if hasattr(self.pricing_crew, 'get_crew') and self.pricing_crew.get_crew() is None:
                print("⚠️  Warning: Crew modules not fully implemented yet.")
        except Exception as e:
            print(f"❌ Error initializing crew: {str(e)}")
            print("⚠️  Some modules may be missing. The application will use fallback behavior.")
    
    async def process_pricing_request(self, product_name: str, specifications: str = "") -> Dict[str, Any]:
        """
        Process a pricing request through the multi-agent workflow.
        
        Args:
            product_name (str): Name of the electronic device
            specifications (str): Additional product specifications
            
        Returns:
            Dict[str, Any]: Complete pricing analysis results
        """
        try:
            # Validate input
            product_input = ProductInput(
                product_name=product_name,
                specifications=specifications,
                category="electronics"
            )
            
            if not self.validator.validate_product_input(product_input):
                return {
                    "success": False,
                    "error": "Invalid product input. Please check your product name and specifications."
                }
            
            print(f"🚀 Starting pricing analysis for: {product_name}")
            print(f"📋 Specifications: {specifications if specifications else 'None provided'}")
            print("-" * 60)
            
            # Prepare input data for the crew
            crew_inputs = {
                "product_name": product_name,
                "specifications": specifications,
                "max_websites": 3,
                "category": "electronics"
            }
            
            # Execute the crew workflow
            print("🔄 Executing multi-agent workflow...")
            result = await self._execute_crew_workflow(crew_inputs)
            
            if result.get("success", False):
                # Process and format the results
                processed_result = self.data_processor.format_pricing_results(result)
                
                print("✅ Pricing analysis completed successfully!")
                self._display_results(processed_result)
                
                return processed_result
            else:
                print(f"❌ Pricing analysis failed: {result.get('error', 'Unknown error')}")
                return result
                
        except Exception as e:
            error_msg = f"Error processing pricing request: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    async def _execute_crew_workflow(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the CrewAI workflow with all agents.
        
        Args:
            inputs (Dict[str, Any]): Input data for the crew
            
        Returns:
            Dict[str, Any]: Workflow execution results
        """
        try:
            # Get the configured crew
            crew = self.pricing_crew.get_crew()
            
            if crew is None:
                return {
                    "success": False,
                    "error": "Crew not properly initialized. Please implement all required modules."
                }
            
            # Execute the crew workflow
            print("👥 Agents are working...")
            print("🕷️  Competitor Scraper: Searching for product prices...")
            print("🎯 Price Optimizer: Analyzing pricing strategies...")
            print("📊 Impact Simulator: Simulating market impact...")
            
            # Run the crew (this will execute all tasks in sequence)
            result = crew.kickoff(inputs=inputs)
            
            # Process the crew result
            if hasattr(result, 'raw'):
                # If result is a CrewOutput object
                return {
                    "success": True,
                    "raw_output": result.raw,
                    "tasks_output": [task.raw for task in result.tasks_output] if hasattr(result, 'tasks_output') else [],
                    "timestamp": self.data_processor.get_timestamp()
                }
            else:
                # If result is already a dict or string
                return {
                    "success": True,
                    "raw_output": str(result),
                    "timestamp": self.data_processor.get_timestamp()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Crew execution failed: {str(e)}"
            }
    
    def _display_results(self, results: Dict[str, Any]):
        """
        Display the pricing analysis results in a formatted way.
        
        Args:
            results (Dict[str, Any]): Processed results to display
        """
        print("\n" + "="*80)
        print("📊 DYNAMIC PRICING ANALYSIS RESULTS")
        print("="*80)
        
        if "competitor_data" in results:
            print("\n🏪 COMPETITOR PRICING DATA:")
            for competitor in results["competitor_data"]:
                print(f"  • {competitor.get('website', 'Unknown')}: ${competitor.get('price', 'N/A')}")
        
        if "optimization_strategy" in results:
            print(f"\n🎯 RECOMMENDED PRICING STRATEGY:")
            strategy = results["optimization_strategy"]
            print(f"  • Suggested Price: ${strategy.get('suggested_price', 'N/A')}")
            print(f"  • Strategy Type: {strategy.get('strategy_type', 'N/A')}")
            print(f"  • Reasoning: {strategy.get('reasoning', 'N/A')}")
        
        if "impact_simulation" in results:
            print(f"\n📈 MARKET IMPACT SIMULATION:")
            impact = results["impact_simulation"]
            print(f"  • Expected Revenue Change: {impact.get('revenue_change', 'N/A')}")
            print(f"  • Market Position: {impact.get('market_position', 'N/A')}")
            print(f"  • Risk Assessment: {impact.get('risk_level', 'N/A')}")
        
        print("\n" + "="*80)
    
    def interactive_mode(self):
        """Run the assistant in interactive mode."""
        print("\n🤖 Dynamic Pricing Assistant - Interactive Mode")
        print("="*60)
        print("Enter electronic device details for pricing analysis.")
        print("Type 'quit' or 'exit' to stop.\n")
        
        while True:
            try:
                # Get product input
                product_name = input("📱 Product Name: ").strip()
                
                if product_name.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not product_name:
                    print("⚠️  Please enter a valid product name.")
                    continue
                
                specifications = input("📋 Specifications (optional): ").strip()
                
                # Process the request
                result = asyncio.run(self.process_pricing_request(product_name, specifications))
                
                if not result.get("success", False):
                    print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                
                print("\n" + "-"*60)
                print("Ready for next analysis...\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                continue


def main():
    """Main function to run the Dynamic Pricing Assistant."""
    print("🚀 Starting Dynamic Pricing Assistant...")
    
    # Check environment variables
    required_env_vars = ['GEMINI_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these environment variables before running the application.")
        print("\n📋 You can set them by:")
        print("1. Creating a .env file in the project root with:")
        print("   GEMINI_API_KEY=your_api_key_here")
        print("2. Or setting them in PowerShell:")
        print("   $env:GEMINI_API_KEY=\"your_api_key_here\"")
        print("\n🔑 Get your API keys from:")
        print("• Gemini: https://makersuite.google.com/app/apikey")
        print("• Pinecone: https://app.pinecone.io/")
        print("• Serper: https://serper.dev/")
        sys.exit(1)
    
    try:
        # Initialize the assistant
        assistant = DynamicPricingAssistant()
        
        # Check command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == '--interactive' or sys.argv[1] == '-i':
                # Interactive mode
                assistant.interactive_mode()
            elif sys.argv[1] == '--help' or sys.argv[1] == '-h':
                print_help()
            else:
                # Single product analysis
                product_name = sys.argv[1]
                specifications = sys.argv[2] if len(sys.argv) > 2 else ""
                
                result = asyncio.run(assistant.process_pricing_request(product_name, specifications))
                
                if not result.get("success", False):
                    print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                    sys.exit(1)
        else:
            # Default to interactive mode
            assistant.interactive_mode()
            
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)


def print_help():
    """Print help information."""
    help_text = """
Dynamic Pricing Assistant - Help

Usage:
  python main.py                           # Interactive mode
  python main.py -i/--interactive          # Interactive mode
  python main.py "iPhone 15" "128GB"       # Single analysis
  python main.py -h/--help                 # Show this help

Environment Variables Required:
  GEMINI_API_KEY      # Google Gemini API key
  PINECONE_API_KEY    # Pinecone vector database API key
  PINECONE_ENV        # Pinecone environment (optional)

Examples:
  python main.py "Samsung Galaxy S24" "256GB, Unlocked"
  python main.py "MacBook Air" "M2 chip, 8GB RAM"
  python main.py "Sony WH-1000XM5" "Noise Cancelling Headphones"

Features:
  • Web scraping of competitor prices (limited to 3 websites)
  • AI-powered price optimization strategies
  • Market impact simulation
  • Vector database storage for price history
  • Electronic devices category focus
    """
    print(help_text)


if __name__ == "__main__":
    main()