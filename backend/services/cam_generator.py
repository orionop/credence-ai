import logging
import json
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.2)

CAM_PROMPT = """
You are an expert Credit Manager at a top-tier Indian Corporate Bank (e.g., HDFC, ICICI, Kotak).
Your task is to generate a comprehensive Credit Appraisal Memo (CAM) for the entity "{company_name}".

**Context**:
- **Requested Loan Amount**: {loan_amount}
- **Sector**: {sector}

**Inputs for Analysis**:
1. **Financial Highlights (Structured)**:
{financials}

2. **GST Behavioral & Integrity Metrics**:
{gst_data}

3. **Secondary Market Research (Autonomous Agent Results)**:
{insights}

4. **Primary Field Observations (Credit Officer Notes)**:
{primary_insights}

**Report Requirements**:
1. Use professional Indian banking terminology.
2. Structure the report using the "Five Cs of Credit":
   - **Character**: Evaluation of promoters, litigation risk, and integrity flags.
   - **Capacity**: Analysis of cash flows, debt serviceability, and GST tax-to-revenue ratios.
   - **Capital**: Net worth assessment and leverage.
   - **Collateral**: Proposed security and asset coverage.
   - **Conditions**: Macro/sector headwinds vs. entity positioning.
3. **Specific Analysis**:
   - Compare "Declared GST Turnover" vs "Audited Revenue" if variance is provided.
   - Flag any ITC Mismatch or high ITC Dependency.
4. **Final Recommendation**:
   - **Sanction Status**: Approved/Rejected/Conditional.
   - **Sanction Amount**: Recommend an amount based on the {loan_amount} requested.
   - **Pricing**: Risk-adjusted interest rate (e.g., 1-year MCLR + 250 bps).
   - **Covenants**: Specific financial or non-financial conditions (e.g., DSCR > 1.2x).

Tone: Highly objective, data-driven, and authoritative.
"""

def generate_cam(
    company_name: str, 
    financials: dict, 
    insights: list, 
    primary_insights: str = "",
    loan_amount: str = "Not Specified",
    sector: str = "Unknown",
    rich_gst_data: dict = None
) -> str:
    """
    Synthesizes all gathered intelligence into a high-stakes appraisal memo.
    """
    logger.info(f"Generating professional CAM for {company_name}")
    
    try:
        financials_str = json.dumps(financials, indent=2)
        gst_str = json.dumps(rich_gst_data, indent=2) if rich_gst_data else "No rich GST behavioral data available."
        insights_str = "\n".join([f"- {i}" for i in insights])
        
        prompt = PromptTemplate.from_template(CAM_PROMPT)
        formatted_prompt = prompt.format(
            company_name=company_name,
            loan_amount=loan_amount,
            sector=sector,
            financials=financials_str,
            gst_data=gst_str,
            insights=insights_str,
            primary_insights=primary_insights if primary_insights else "None provided."
        )
        
        response = llm.invoke([HumanMessage(content=formatted_prompt)])
        return response.content
        
    except Exception as e:
        logger.error(f"Error generating CAM: {e}")
        return f"# Credit Appraisal Memo (CAM) - {company_name}\n\nError generating advanced report: {str(e)}"

