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
You are an expert Credit Manager at a top-tier Indian Corporate Bank.
Your task is to generate a comprehensive Credit Appraisal Memo (CAM) for the entity "{company_name}".

You are provided with:
1. Structured Financials (extracted from filings):
{financials}

2. Secondary Research Insights (web crawl data):
{insights}

3. Primary Field Insights (qualitative notes from due diligence):
{primary_insights}

Generate a professional Markdown report structured with the "Five Cs of Credit" (Character, Capacity, Capital, Collateral, and Conditions).
At the end, provide a definitive "Final Recommendation":
- Suggest whether to lend or reject.
- Explain the transparent logic behind this decision based on the provided inputs (especially flagging any litigation or related-party risks).
- If lending, suggest a risk-adjusted framework (e.g. "Approved with 2% risk premium due to X").

Keep the tone highly professional, objective, and analytical. Use bullet points and bold text where appropriate.
"""

def generate_cam(company_name: str, financials: dict, insights: list, primary_insights: str = "") -> str:
    """
    Real implementation of the final Credit Appraisal Memo generator using LLM.
    Synthesizes structured numbers, agent insights, and primary feedback.
    """
    logger.info(f"Generating CAM for {company_name}")
    
    try:
        financials_str = json.dumps(financials, indent=2)
        insights_str = "\n".join([f"- {i}" for i in insights])
        
        prompt = PromptTemplate.from_template(CAM_PROMPT)
        formatted_prompt = prompt.format(
            company_name=company_name,
            financials=financials_str,
            insights=insights_str,
            primary_insights=primary_insights if primary_insights else "None provided."
        )
        
        response = llm.invoke([HumanMessage(content=formatted_prompt)])
        return response.content
        
    except Exception as e:
        logger.error(f"Error generating CAM: {e}")
        
        # Fallback
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"""# Credit Appraisal Memo (CAM)
**Entity:** {company_name}
**Date:** {date_str}

## Error Generating Advanced CAM
An error occurred while connecting to the AI models: {str(e)}

### Interim Financials
{financials}
"""
