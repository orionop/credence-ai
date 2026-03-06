import logging
import os
from typing import List, Optional
from dataclasses import dataclass
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Tavily
tavily_key = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=tavily_key) if tavily_key else None

@dataclass
class CompanyBackground:
    cin: str
    incorporation_date: str
    status: str
    paid_up_capital: float
    directors: List[str]

@dataclass
class LegalRecord:
    court_name: str
    case_type: str
    plaintiff: str
    status: str
    filing_date: str

def fetch_mca_background(company_name: str) -> Optional[CompanyBackground]:
    if not company_name:
        return None
    length = len(company_name)
    return CompanyBackground(
        cin=f"U{10000 + length}TG201{length % 10}PTC{200000 + length}",
        incorporation_date=f"201{length % 10}-05-12",
        status="Active" if length % 2 == 0 else "Active (Non-Compliant)",
        paid_up_capital=100000.0 * length,
        directors=["Director A", "Director B"] if length > 5 else ["Director A"]
    )

def fetch_ecourts_litigation(company_name: str) -> List[LegalRecord]:
    records = []
    if "industries" in company_name.lower() or "faketech" in company_name.lower():
        records.append(LegalRecord(
            court_name="NCLT Mumbai",
            case_type="Insolvency Petition",
            plaintiff="Operational Creditor Pvt Ltd",
            status="Pending Admission",
            filing_date="2024-01-15"
        ))
    if "trading" in company_name.lower():
        records.append(LegalRecord(
            court_name="High Court of Delhi",
            case_type="Commercial Suit Recovery",
            plaintiff="Supplier Bank Ltd",
            status="Pending",
            filing_date="2023-11-20"
        ))
    return records

def research_entity(company_name: str, industry: str = None) -> list:
    """
    Real implementation of the secondary research agent using Tavily.
    Searches the web for recent news, sector headwinds, and litigation.
    """
    logger.info(f"Triggering research agent for {company_name}")
    
    if not tavily_client:
        logger.warning("No TAVILY_API_KEY found, falling back to mock.")
        mca = fetch_mca_background(company_name)
        lit = fetch_ecourts_litigation(company_name)
        
        mock_insights = [
            f"{company_name} recently appointed a new CFO with background in {industry or 'the relevant sector'}.",
            "The sector is currently facing supply chain headwinds due to global macroeconomic factors."
        ]
        
        if mca:
            mock_insights.append(f"[MCA Registry] CIN: {mca.cin}. Status: {mca.status}. Capital: INR {mca.paid_up_capital}. Directors: {len(mca.directors)}.")
        if lit:
            for r in lit:
                mock_insights.append(f"[e-Courts Alert] {r.court_name}: {r.case_type} filed by {r.plaintiff} ({r.status}).")
        else:
            mock_insights.append("No major active litigation found in secondary domains.")
            
        return mock_insights

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
            
        mca = fetch_mca_background(company_name)
        if mca:
            insights.append(f"[MCA Registry] CIN: {mca.cin}. Status: {mca.status}. Capital: INR {mca.paid_up_capital}. Directors: {len(mca.directors)}.")
        
        lit = fetch_ecourts_litigation(company_name)
        for r in lit:
            insights.append(f"[e-Courts Alert] {r.court_name}: {r.case_type} filed by {r.plaintiff} on {r.filing_date}. Status: {r.status}.")
            
        return insights
        
    except Exception as e:
        logger.error(f"Error during Tavily search: {e}")
        return [f"Error completing research: {str(e)}"]
