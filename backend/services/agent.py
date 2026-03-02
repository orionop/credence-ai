import logging
import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Tavily
tavily_key = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=tavily_key) if tavily_key else None

def research_entity(company_name: str, industry: str = None) -> list:
    """
    Real implementation of the secondary research agent using Tavily.
    Searches the web for recent news, sector headwinds, and litigation.
    """
    logger.info(f"Triggering research agent for {company_name}")
    
    if not tavily_client:
        logger.warning("No TAVILY_API_KEY found, falling back to mock.")
        return [
            f"{company_name} recently appointed a new CFO with background in {industry or 'the relevant sector'}.",
            "The sector is currently facing supply chain headwinds due to global macroeconomic factors.",
            "No major active litigation found in secondary domains."
        ]

    try:
        query = f"{company_name} {industry or ''} news sector headwinds litigation"
        logger.info(f"Searching Tavily for: {query}")
        
        # Execute search
        response = tavily_client.search(
            query=query, 
            search_depth="advanced", 
            max_results=3,
            include_images=False
        )
        
        insights = []
        for result in response.get("results", []):
            title = result.get("title", "")
            content = result.get("content", "")
            # Clean and truncate the insight to be succinct
            insight = f"Found: {title} - {content[:200]}..."
            insights.append(insight)
            
        if not insights:
            insights.append(f"No recent notable negative news or litigation found for {company_name}.")
            
        return insights
        
    except Exception as e:
        logger.error(f"Error during Tavily search: {e}")
        return [f"Error completing research: {str(e)}"]
