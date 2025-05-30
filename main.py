import streamlit as st
import pandas as pd
from agents.competitor_scraper import CompetitorScraperAgent
from agents.price_optimizer import PriceOptimizerAgent
from agents.impact_simulator import ImpactSimulatorAgent
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO, filename="app.log")
logger = logging.getLogger(__name__)

def main():
    st.set_page_config(page_title="Dynamic Pricing Assistant", layout="wide")
    
    # Custom CSS for styling
    st.markdown("""
        <style>
        .main-title { font-size: 2.5em; color: #1f77b4; }
        .section-header { font-size: 1.5em; color: #2ca02c; margin-top: 20px; }
        .status-box { background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
        .stButton>button { background-color: #1f77b4; color: white; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title">Dynamic Pricing Assistant</div>', unsafe_allow_html=True)
    
    # Input form
    with st.form(key="pricing_form"):
        col1, col2 = st.columns(2)
        with col1:
            product_name = st.text_input("Product Name", value="samsung", help="Enter the product name to analyze")
        with col2:
            specifications = st.text_input("Specifications", value="S9000", help="Enter product specifications")
        submit_button = st.form_submit_button("Analyze Pricing", help="Click to start the pricing analysis")

    # Process flow visualization
    st.markdown('<div class="section-header">Process Flow</div>', unsafe_allow_html=True)
    st.markdown("""
    1. **Scrape Competitors**: Collect pricing data from competitors.
    2. **Optimize Price**: Analyze data and suggest an optimal price.
    3. **Simulate Impact**: Predict the impact of the suggested price.
    """)

    if submit_button:
        try:
            query = f"Product: {product_name}, Specifications: {specifications}"
            logger.info(f"Processing query: {query}")
            
            # Status display
            status_placeholder = st.empty()
            progress_bar = st.progress(0)
            
            # Initialize agents
            status_placeholder.markdown('<div class="status-box">Initializing agents...</div>', unsafe_allow_html=True)
            time.sleep(0.5)  # Simulate initialization
            scraper_agent = CompetitorScraperAgent()
            optimizer_agent = PriceOptimizerAgent()
            simulator_agent = ImpactSimulatorAgent()
            progress_bar.progress(20)
            
            # Scrape competitors
            status_placeholder.markdown('<div class="status-box">Scraping competitor data...</div>', unsafe_allow_html=True)
            scraper_result = scraper_agent.run(query)
            products = scraper_result.get("products", [])
            progress_bar.progress(50)
            
            # Display competitor pricing
            st.markdown('<div class="section-header">Competitor Pricing</div>', unsafe_allow_html=True)
            if products:
                df = pd.DataFrame(products)
                st.dataframe(df[['product_name', 'price']], use_container_width=True)
            else:
                st.warning("No competitor prices found.")
            
            # Optimize price
            status_placeholder.markdown('<div class="status-box">Optimizing price...</div>', unsafe_allow_html=True)
            optimizer_result = optimizer_agent.run(query, partial_data=products)
            progress_bar.progress(80)
            
            # Display pricing strategy
            st.markdown('<div class="section-header">Pricing Strategy</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Suggested Price", f"${optimizer_result['suggested_price']:.2f}")
            with col2:
                st.write(f"**Strategy**: {optimizer_result['strategy']}")
            
            # Simulate impact
            status_placeholder.markdown('<div class="status-box">Simulating price impact...</div>', unsafe_allow_html=True)
            simulator_result = simulator_agent.run(query, suggested_price=optimizer_result['suggested_price'])
            progress_bar.progress(100)
            
            # Display impact simulation
            st.markdown('<div class="section-header">Impact Simulation</div>', unsafe_allow_html=True)
            st.write(f"**Impact**: {simulator_result['impact']}")
            
            status_placeholder.markdown('<div class="status-box">Analysis complete!</div>', unsafe_allow_html=True)
            
        except Exception as e:
            logger.error(f"Main error: {e}")
            st.error(f"Error: {str(e)}")
            progress_bar.progress(0)
            status_placeholder.empty()

if __name__ == "__main__":
    main()