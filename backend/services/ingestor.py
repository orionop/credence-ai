"""
Document AI Ingestor — Powered by Google Gemini 1.5 Flash.
Parses PDFs (GST, CIBIL, Annual Reports, Bank Statements) and extracts
structured JSON using specialized prompts per document type.
Falls back to OpenAI GPT-3.5 if Gemini is unavailable.
"""

import logging
import fitz  # PyMuPDF
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── LLM Setup ───────────────────────────────────────────────────────────────

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

_llm = None

def get_llm():
    """Lazy-init the LLM — prefer Gemini, fall back to OpenAI."""
    global _llm
    if _llm is not None:
        return _llm

    if GOOGLE_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            _llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=GOOGLE_API_KEY,
                temperature=0,
            )
            logger.info("Using Google Gemini 1.5 Flash for document parsing")
            return _llm
        except Exception as e:
            logger.warning(f"Gemini init failed ({e}), falling back to OpenAI")

    # Fallback to OpenAI
    from langchain_openai import ChatOpenAI
    _llm = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0).bind(
        response_format={"type": "json_object"}
    )
    logger.info("Using OpenAI GPT-3.5 for document parsing")
    return _llm


# ── Document Type Detection ─────────────────────────────────────────────────

def detect_doc_type(filename: str, text: str) -> str:
    """Heuristically detect document type from filename and content."""
    fname = filename.lower()
    text_lower = text[:3000].lower()

    if any(k in fname for k in ['gst', 'gstr', 'gstin']):
        return 'GST'
    if any(k in text_lower for k in ['gstin', 'gstr-3b', 'gstr-2a', 'gstr-1',
                                       'output tax', 'input tax credit', 'itc',
                                       'reverse charge', 'taxable supplies']):
        return 'GST'

    if any(k in fname for k in ['cibil', 'ccr', 'credit_report']):
        return 'CIBIL'
    if any(k in text_lower for k in ['cibil', 'credit information bureau',
                                       'ccr rank', 'payment history', 'suit filed']):
        return 'CIBIL'

    if any(k in fname for k in ['bank', 'statement', 'passbook']):
        return 'BANK_STATEMENT'
    if any(k in text_lower for k in ['opening balance', 'closing balance',
                                       'debit', 'credit', 'bank statement']):
        return 'BANK_STATEMENT'

    if any(k in fname for k in ['itr', 'income_tax', 'return']):
        return 'ITR'

    # Default for annual reports, board minutes, etc.
    return 'ANNUAL_REPORT'


# ── Specialized Prompts ──────────────────────────────────────────────────────

GST_EXTRACTION_PROMPT = """
You are a senior chartered accountant analyzing a GST Compliance Statement.
Extract ALL financial metrics from this document into the EXACT JSON schema below.
If a value is not found, use null. All monetary values should be in raw numbers (not formatted strings).

Return ONLY valid JSON with this exact structure:
{{
  "company_financials": {{
    "total_revenue": null,
    "total_debt": null,
    "contingent_liabilities": null
  }},
  "gst_behavioral_cash_metrics": {{
    "gst_declared_supplies": null,
    "domestic_supplies": null,
    "export_supplies": null,
    "output_tax_liability": null,
    "output_tax_breakdown": {{
      "cgst": null,
      "sgst": null,
      "igst": null
    }},
    "gross_tax_obligation": null,
    "gst_itc_claimed": null,
    "gst_itc_supplier": null,
    "gst_itc_variance": null,
    "itc_utilized": null,
    "cash_tax_paid": null,
    "credit_notes_value": null,
    "credit_note_tax_reduction": null,
    "reverse_charge_freight": null,
    "reverse_charge_legal": null,
    "interest_and_late_fees_paid": null,
    "refund_claimed": null,
    "refund_sanctioned": null,
    "pending_refunds": null
  }},
  "document_risks": {{
    "document_risk_mentions": [
      {{"type": "<risk type>", "amount": null}}
    ],
    "legal_litigations": []
  }},
  "gst_risk_features": {{
    "itc_utilization_ratio": null,
    "refund_approval_ratio": null,
    "cash_to_itc_ratio": null,
    "cash_tax_ratio": null,
    "output_tax_to_revenue_ratio": null,
    "credit_note_percentage": null,
    "itc_mismatch_ratio": null,
    "itc_dependency_ratio": null,
    "cash_to_gross_tax_ratio": null,
    "refund_intensity_ratio": null,
    "document_risk_intensity": null,
    "flag_100_percent_itc_utilization": false,
    "risk_flags": []
  }}
}}

Document Text:
{text}
"""

CIBIL_EXTRACTION_PROMPT = """
Analyze the following CIBIL Commercial Credit Report (CCR) and extract key metrics.
Return ONLY valid JSON:
{{
  "metadata": {{
    "doc_type": "CIBIL Commercial Report",
    "pages": null
  }},
  "financials": {{
    "ccr_rank": "N/A",
    "credit_score": "N/A",
    "total_credit_facilities": "N/A",
    "overdue_amount": "N/A",
    "suit_filed_amount": "N/A",
    "wilful_default": "N/A"
  }},
  "flags": [],
  "payment_history": {{
    "dpd_30_count": 0,
    "dpd_60_count": 0,
    "dpd_90_count": 0,
    "current_facilities": 0,
    "closed_facilities": 0
  }}
}}

If a value is not found, use "N/A" for strings and 0 for numbers.
Flag items like: "Suit Filed", "Wilful Default", "High DPD", "Multiple Overdue Accounts".

Document Text:
{text}
"""

GENERAL_EXTRACTION_PROMPT = """
Analyze the following text extracted from a corporate document.
Extract key financial indicators and any critical flags or risks.

Return ONLY valid JSON with this exact structure:
{{
  "metadata": {{
    "doc_type": "<Doc Type>",
    "pages": null
  }},
  "financials": {{
    "revenue_yoy_growth": "N/A",
    "ebitda_margin": "N/A",
    "debt_to_equity": "N/A",
    "pat_margin": "N/A",
    "current_ratio": "N/A",
    "interest_coverage": "N/A"
  }},
  "flags": []
}}

If a financial value is not found, use "N/A".
Find flags such as auditor changes, related party transactions, qualified opinions, or liquidity issues.

Document Text:
{text}
"""


# ── PDF Text Extraction ─────────────────────────────────────────────────────

def extract_text_from_pdf(content: bytes, max_pages: int = 20) -> str:
    """Extract text from the first N pages of a PDF."""
    try:
        doc = fitz.open(stream=content, filetype="pdf")
        text = ""
        for i in range(min(len(doc), max_pages)):
            text += doc[i].get_text()
        return text
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return ""


# ── Main Processing ─────────────────────────────────────────────────────────

def process_document(filename: str, content: bytes) -> dict:
    """
    Process document: extract text, detect type, use specialized LLM prompt.
    Returns structured JSON matching the document type schema.
    """
    logger.info(f"Processing document {filename} ({len(content)} bytes)")

    # 1. Extract text
    text = ""
    if filename.lower().endswith('.pdf'):
        text = extract_text_from_pdf(content)
    else:
        text = content.decode('utf-8', errors='ignore')[:15000]

    if not text.strip():
        logger.warning("No text extracted from document.")
        text = "Empty or unreadable document."

    # 2. Detect document type
    doc_type = detect_doc_type(filename, text)
    logger.info(f"Detected document type: {doc_type}")

    # 3. Select prompt
    if doc_type == 'GST':
        prompt_template = GST_EXTRACTION_PROMPT
    elif doc_type == 'CIBIL':
        prompt_template = CIBIL_EXTRACTION_PROMPT
    else:
        prompt_template = GENERAL_EXTRACTION_PROMPT

    # 4. Call LLM
    try:
        llm = get_llm()
        formatted_prompt = prompt_template.format(text=text[:20000])

        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content=formatted_prompt)])

        # Parse response — handle markdown-wrapped JSON
        response_text = response.content.strip()
        if response_text.startswith("```"):
            response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)

        structured_data = json.loads(response_text)

        # Tag the doc type
        if doc_type == 'GST':
            structured_data["_doc_type"] = "GST"
            # Also build a simplified financials dict for backward compat
            gst = structured_data.get("gst_behavioral_cash_metrics", {})
            cf = structured_data.get("company_financials", {})
            structured_data["metadata"] = {"doc_type": "GST Compliance Statement", "pages": None}
            structured_data["financials"] = {
                "revenue_yoy_growth": "N/A",
                "ebitda_margin": "N/A",
                "debt_to_equity": "N/A",
                "gst_turnover": gst.get("gst_declared_supplies"),
                "itc_claimed": gst.get("gst_itc_claimed"),
                "itc_variance": gst.get("gst_itc_variance"),
                "cash_tax_paid": gst.get("cash_tax_paid"),
                "total_revenue": cf.get("total_revenue"),
            }
            # Build flags from risk features
            risk = structured_data.get("gst_risk_features", {})
            structured_data["flags"] = risk.get("risk_flags", [])
        elif doc_type == 'CIBIL':
            structured_data["_doc_type"] = "CIBIL"
        else:
            structured_data["_doc_type"] = doc_type
            structured_data.setdefault("metadata", {})["doc_type"] = doc_type

        return structured_data

    except Exception as e:
        logger.error(f"Error during LLM extraction: {e}")
        return {
            "_doc_type": doc_type,
            "metadata": {"doc_type": doc_type, "pages": 1},
            "financials": {"revenue_yoy_growth": "N/A", "ebitda_margin": "N/A", "debt_to_equity": "N/A"},
            "flags": [f"LLM Extraction Failed: {str(e)[:80]}"]
        }
