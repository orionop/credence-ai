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

try:
    from .document_ai.layout_parser import parse_document_layouts
except ImportError:
    parse_document_layouts = None

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

    if any(k in fname for k in ['sanction', 'loan', 'facility']):
        return 'SANCTION_LETTER'
    if any(k in text_lower for k in ['sanction letter', 'facility agreement', 'sanctioned amount']):
        return 'SANCTION_LETTER'

    # Default for annual reports, board minutes, etc.
    return 'ANNUAL_REPORT'


# ── Specialized Prompts ──────────────────────────────────────────────────────

from services.anomaly_detector import detector

# ── Behavioral Risk Math ───────────────────────────────────────────────────

def derive_behavioral_risk(raw_json: dict) -> dict:
    """
    Calculates behavioral fraud indicators locally to avoid LLM math hallucinations.
    Logic ported and refined from Layout-Aware Parser logic.
    """
    features = {}
    metrics = raw_json.get("gst_behavioral_cash_metrics", {})
    if not metrics:
        return {}
        
    def safe_div(num, den):
        try:
            if num is None or den is None or float(den) == 0:
                return 0.0
            return round(float(num) / float(den), 4)
        except:
            return 0.0

    gst_declared = metrics.get("gst_declared_supplies", 0)
    itc_claimed = metrics.get("gst_itc_claimed", 0)
    itc_utilized = metrics.get("itc_utilized", 0)
    output_tax = metrics.get("output_tax_liability", 0)
    cash_paid = metrics.get("cash_tax_paid", 0)

    features["itc_utilization_ratio"] = safe_div(itc_utilized, itc_claimed)
    features["cash_to_itc_ratio"] = safe_div(cash_paid, itc_utilized)
    features["cash_tax_ratio"] = safe_div(cash_paid, output_tax)
    features["output_tax_to_revenue_ratio"] = safe_div(output_tax, gst_declared)
    features["itc_mismatch_ratio"] = safe_div(metrics.get("gst_itc_variance"), metrics.get("gst_itc_supplier"))
    features["itc_dependency_ratio"] = safe_div(itc_utilized, output_tax)
    
    # Advanced logic: 100% ITC utilization is a major audit flag in India
    features["flag_100_percent_itc_utilization"] = (features.get("itc_utilization_ratio") >= 0.99)
    
    risk_flags = []
    if features["flag_100_percent_itc_utilization"]:
        risk_flags.append("CRITICAL: 100% ITC Utilization (Auditor Alert)")
    if features["cash_tax_ratio"] < 0.05:
        risk_flags.append("HIGH RISK: Minimal Cash Tax Payout")
    if features["itc_mismatch_ratio"] > 0.10:
        risk_flags.append("ITC_RECONCILIATION_VARIANCE_HIGH")
        
    features["risk_flags"] = risk_flags
    
    # Run Hard Math Anomaly Detection (Isolation Forest)
    # Uses: Mismatch, Bank-to-GST, and Velocity (approximated here for single doc)
    anomaly_result = detector.predict(
        gstr_3b=gst_declared or 0,
        gstr_2a=metrics.get("gst_itc_supplier") or 0,
        bank_in=gst_declared * 1.05 if gst_declared else 0, # Placeholder until bank parsing is split
        bank_out=gst_declared * 0.95 if gst_declared else 0
    )
    features["anomaly_detection"] = anomaly_result

    return features

# ── Specialized Prompts ──────────────────────────────────────────────────────

GST_EXTRACTION_PROMPT = """
You are an expert Corporate Credit Analyst/CA evaluating Indian GST Compliance documents.
Extract ALL financial metrics from this document into the EXACT JSON schema below.

CRITICAL AUDIT RULES:
1. STRONGLY ENFORCE: Convert all formatted numbers (with commas) to raw INR integers (e.g., 21,95,00,000 -> 219500000).
2. For Output Tax: Extract the CGST, SGST, IGST split exactly. If missing, use null.
3. If a value is not found, use null.

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

# ── Local RegEx / Keyword Extractions ────────────────────────────────────────

def extract_unstructured_risk_signals(text: str) -> dict:
    """Keyword scan for litigation/default/pledge/downgrade."""
    text_lower = text.lower()
    raw_sentences = text_lower.replace("\n", " ")
    sentences = [s.strip() for s in raw_sentences.split(".") if s.strip()]

    risk_keywords = {
        "litigation": ["litigation", "suit filed", "court case", "arbitration"],
        "default": ["default", "overdue", "npa", "non-performing"],
        "pledge": ["pledge", "pledged shares", "encumbered"],
        "downgrade": ["rating downgrade", "downgraded", "negative outlook"],
    }

    scores = {}
    total_hits = 0
    sample_sentences = {k: [] for k in risk_keywords}

    for key, words in risk_keywords.items():
        hits = 0
        for sent in sentences:
            if any(w in sent for w in words):
                if "no " + key in sent or "without any " + key in sent:
                    continue
                hits += 1
                if len(sample_sentences[key]) < 3:
                    sample_sentences[key].append(sent.strip())
        scores[f"{key}_hits"] = hits
        total_hits += hits

    litigation_hits = scores.get("litigation_hits", 0) + scores.get("default_hits", 0)
    litigation_risk_score = min(1.0, litigation_hits / 10.0) if total_hits > 0 else 0.0

    if litigation_risk_score == 0: severity = "NONE"
    elif litigation_risk_score < 0.3: severity = "LOW"
    elif litigation_risk_score < 0.7: severity = "MEDIUM"
    else: severity = "HIGH"

    return {
        "unstructured_total_hits": total_hits,
        "litigation_risk_score": float(litigation_risk_score),
        "litigation_severity": severity,
        "litigation_sample_sentences": sample_sentences.get("litigation", []),
        "default_sample_sentences": sample_sentences.get("default", []),
        "pledge_sample_sentences": sample_sentences.get("pledge", []),
        "downgrade_sample_sentences": sample_sentences.get("downgrade", []),
        **scores,
    }

def extract_sanction_features(text: str) -> dict:
    """Regex extraction of loan terms, facility type, guarantee flags."""
    lowered = text.lower()
    
    amount_patterns = [
        r"(loan amount|sanction(?:ed)? amount|amount sanctioned)[^\d]{0,40}([\d,]+(?:\.\d+)?)",
        r"amount of\s+rs\.?\s*([\d,]+(?:\.\d+)?)"
    ]
    loan_amount = None
    for pat in amount_patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            try:
                loan_amount = float(m.group(2 if m.lastindex >= 2 else 1).replace(",", ""))
                break
            except ValueError:
                pass

    rate_patterns = [
        r"(interest rate|roi)[^\d]{0,40}(\d{1,2}(?:\.\d+)?)\s*%",
        r"(\d{1,2}(?:\.\d+)?)\s*%\s*(?:p\.?a\.?|per annum)"
    ]
    interest_rate = None
    for pat in rate_patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            try:
                interest_rate = float(m.group(2 if m.lastindex >= 2 else 1))
                break
            except ValueError:
                pass

    tenure_months = None
    for pat in [r"(tenure|tenor|loan period)[^\d]{0,40}(\d{1,3})\s*(months?|mths?)",
                r"(tenure|tenor|loan period)[^\d]{0,40}(\d{1,2})\s*(years?|yrs?)"]:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            try:
                num = int(m.group(2))
                unit = m.group(3).lower()
                tenure_months = num * 12 if "year" in unit or "yr" in unit else num
                break
            except ValueError:
                pass

    facility_type = next((t for t in ["Term Loan", "Cash Credit", "Overdraft", "Working Capital"] if t.lower() in lowered), None)
    guarantee_type = next((t for t in ["JLG", "CGTMSE", "Collateral Free"] if t.lower() in lowered), None)

    if loan_amount is None:
        return {}
        
    features = {"sanction_loan_amount": float(loan_amount)}
    if interest_rate: features["sanction_interest_rate"] = float(interest_rate)
    if tenure_months: features["sanction_tenure_months"] = int(tenure_months)
    if facility_type: features["sanction_facility_type"] = facility_type
    if guarantee_type: features["sanction_guarantee_type"] = guarantee_type
    
    features["sanction_existing_debt"] = float(loan_amount)
    if interest_rate is not None:
        features["sanction_effective_rate"] = float(interest_rate)
        features["sanction_high_interest_flag"] = interest_rate > 20.0
    if tenure_months is not None:
        features["sanction_short_tenure_flag"] = tenure_months <= 12

    micro_flag = guarantee_type and guarantee_type.upper() == "JLG"
    features["sanction_microfinance_exposure_flag"] = bool(micro_flag)
    features["sanction_group_liability_flag"] = bool(micro_flag)

    return features

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

    # 1. Extract text and detect doc_type
    text = ""
    doc_type = "UNKNOWN"
    
    if filename.lower().endswith('.pdf'):
        text = extract_text_from_pdf(content)
        doc_type = detect_doc_type(filename, text)
        
        # Advanced Layout parsing for dense table-heavy reports
        if parse_document_layouts is not None and doc_type in ['ANNUAL_REPORT', 'BANK_STATEMENT', 'ITR']:
            logger.info(f"Running Advanced ML Document Layout Parser on {filename}...")
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                advanced_text = parse_document_layouts(tmp_path)
                if advanced_text.strip():
                    text = advanced_text
            except Exception as e:
                logger.warning(f"Advanced Document AI failed: {e}. Falling back to PyMuPDF.")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
    else:
        text = content.decode('utf-8', errors='ignore')[:15000]
        doc_type = detect_doc_type(filename, text)

    if not text.strip():
        logger.warning("No text extracted from document.")
        text = "Empty or unreadable document."
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
            
            # Post-Extraction: Drive Behavioral Risk via Local Math (Superior to LLM Math)
            risk_features = derive_behavioral_risk(structured_data)
            structured_data["gst_risk_features"] = risk_features
            
            # Build simplified financials dict for backward compat
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
            structured_data["flags"] = risk_features.get("risk_flags", [])
            
        elif doc_type == 'CIBIL':
            structured_data["_doc_type"] = "CIBIL"
        elif doc_type == 'SANCTION_LETTER':
            structured_data["_doc_type"] = "SANCTION_LETTER"
            sanction_features = extract_sanction_features(text)
            structured_data["sanction_features"] = sanction_features
        else:
            structured_data["_doc_type"] = doc_type
            structured_data.setdefault("metadata", {})["doc_type"] = doc_type

        # Global unstructured risk scan
        unstructured_risks = extract_unstructured_risk_signals(text)
        structured_data["unstructured_risks"] = unstructured_risks
        
        # Merge high-level unstructured flags
        if unstructured_risks.get("litigation_risk_score", 0.0) > 0.0:
            if "flags" not in structured_data:
                structured_data["flags"] = []
            structured_data["flags"].append(f"Unstructured Risk: {unstructured_risks.get('litigation_severity')} severity")

        return structured_data

    except Exception as e:
        logger.error(f"Error during LLM extraction: {e}")
        return {
            "_doc_type": doc_type,
            "metadata": {"doc_type": doc_type, "pages": 1},
            "financials": {"revenue_yoy_growth": "N/A", "ebitda_margin": "N/A", "debt_to_equity": "N/A"},
            "flags": [f"LLM Extraction Failed: {str(e)[:80]}"]
        }
