import logging
import fitz  # PyMuPDF
from io import BytesIO
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
import json
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0).bind(
    response_format={"type": "json_object"}
)

EXTRACTION_PROMPT = """
Analyze the following text extracted from a corporate document (Annual Report or GST Statement).
Extract key financial indicators and any critical flags or risks.

Return a JSON object with this exact structure:
{{
  "metadata": {{
    "doc_type": "<Doc Type>",
    "pages": <Number of pages>
  }},
  "financials": {{
    "revenue_yoy_growth": "<Growth %>",
    "ebitda_margin": "<Margin %>",
    "debt_to_equity": "<Ratio>"
  }},
  "flags": [
    "<Flag 1>", 
    "<Flag 2>"
  ]
}}

If a financial value is not found, use "N/A".
Find flags such as auditor changes, related party transactions, or liquidity issues.

Document Text:
{text}
"""

def extract_text_from_pdf(content: bytes, max_pages: int = 15) -> str:
    """Extract text from the first few pages of a PDF to save tokens."""
    try:
        doc = fitz.open(stream=content, filetype="pdf")
        text = ""
        for i in range(min(len(doc), max_pages)):
            text += doc[i].get_text()
        return text
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return ""

def process_document(filename: str, content: bytes) -> dict:
    """
    Process document, extract text, and use LLM to structure financial numbers.
    """
    logger.info(f"Processing document {filename} of size {len(content)} bytes")
    
    # 1. Extract Text
    text = ""
    if filename.endswith('.pdf'):
        text = extract_text_from_pdf(content)
    else:
        # Fallback for CSVs or text
        text = content.decode('utf-8', errors='ignore')[:10000]

    if not text.strip():
        logger.warning("No text extracted from document.")
        text = "Empty or unreadable document."

    # 2. Extract structured data using LLM
    try:
        prompt = PromptTemplate.from_template(EXTRACTION_PROMPT)
        formatted_prompt = prompt.format(text=text[:15000]) # Cap tokens
        
        response = llm.invoke([HumanMessage(content=formatted_prompt)])
        structured_data = json.loads(response.content)
        
        # Override metadata
        structured_data["metadata"]["doc_type"] = "Annual Report" if filename.endswith('.pdf') else "GST Statement"
        
        return structured_data
        
    except Exception as e:
        logger.error(f"Error during LLM extraction: {e}")
        # Fallback to mock if API fails
        return {
            "metadata": {"doc_type": "PDF", "pages": 1},
            "financials": {"revenue_yoy_growth": "N/A", "ebitda_margin": "N/A", "debt_to_equity": "N/A"},
            "flags": ["LLM Extraction Failed"]
        }
