import streamlit as st
from agents.competitor_scraper import CompetitorScraperAgent
from agents.price_optimizer import PriceOptimizerAgent
from agents.impact_simulator import ImpactSimulatorAgent

def main():
    st.title("Dynamic Pricing Assistant")
    
    # Input form
    product_name = st.text_input("Enter Product Name")
    specifications = st.text_area("Enter Product Specifications")
    
    if st.button("Analyze Pricing"):
        if product_name and specifications:
            # Initialize agents
            scraper_agent = CompetitorScraperAgent()
            optimizer_agent = PriceOptimizerAgent()
            simulator_agent = ImpactSimulatorAgent()
            
            # Step 1: Scrape competitor prices
            st.subheader("Competitor Pricing")
            scraped_data = scraper_agent.run(product_name, specifications)
            st.write(scraped_data)
            
            # Step 2: Optimize pricing
            st.subheader("Pricing Strategy")
            pricing_strategy = optimizer_agent.run(product_name, specifications)
            st.write(pricing_strategy)
            
            # Step 3: Simulate impact
            st.subheader("Impact Simulation")
            impact = simulator_agent.run(pricing_strategy)
            st.write(impact)
        else:
            st.error("Please provide both product name and specifications.")

if __name__ == "__main__":
    main()