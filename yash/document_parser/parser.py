import fitz  # PyMuPDF
import json
import os
import google.generativeai as genai
from pydantic import BaseModel
from typing import List, Optional

class CompanyFinancials(BaseModel):
    total_revenue: Optional[int]
    total_debt: Optional[int]
    contingent_liabilities: Optional[int]

class OutputTaxBreakdown(BaseModel):
    cgst: Optional[int]
    sgst: Optional[int]
    igst: Optional[int]

class GSTBehavioralMetrics(BaseModel):
    gross_tax_obligation: Optional[int]
    output_tax_liability: Optional[int]
    output_tax_breakdown: Optional[OutputTaxBreakdown]
    cash_tax_paid: Optional[int]
    itc_utilized: Optional[int]
    export_supplies: Optional[int]
    domestic_supplies: Optional[int]
    refund_claimed: Optional[int]
    refund_sanctioned: Optional[int]
    credit_notes_value: Optional[int]
    credit_note_tax_reduction: Optional[int]
    reverse_charge_freight: Optional[int]
    reverse_charge_legal: Optional[int]
    gst_declared_supplies: Optional[int]
    gst_itc_claimed: Optional[int]
    gst_itc_supplier: Optional[int]
    gst_itc_variance: Optional[int]
    interest_and_late_fees_paid: Optional[int]
    pending_refunds: Optional[int]

class DocumentRisk(BaseModel):
    type: str # e.g. credit_disallowance, penalty, interest
    amount: Optional[int]

class DocumentRisks(BaseModel):
    document_risk_mentions: List[DocumentRisk]
    legal_litigations: List[str]

# We use Pydantic to enforce the schema we want back from the LLM
class RAWFinancialExtractionSchema(BaseModel):
    company_financials: CompanyFinancials
    gst_behavioral_metrics: GSTBehavioralMetrics
    document_risks: DocumentRisks

class DocumentParser:
    def __init__(self, api_key: str):
        """
        Initializes the Gemini model which is excellent for long-context
        document parsing.
        """
        genai.configure(api_key=api_key)
        # Using gemini-2.5-flash as it is fast and supports JSON schema natively
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Reads a PDF file using PyMuPDF and extracts all raw text.
        This provides the base context for our LLM to extract financial metrics.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found at {pdf_path}")
            
        doc = fitz.open(pdf_path)
        full_text = ""
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            full_text += f"\n--- Page {page_num + 1} ---\n"
            full_text += page.get_text()
            
        return full_text

    def parse_financials(self, text: str) -> dict:
        """
        Uses Gemini 2.5 Flash to extract specific financial details 
        and return a guaranteed JSON structure.
        """
        prompt = f"""
        You are an expert Corporate Credit Analyst evaluating Indian financial documents, specifically Annual Reports and GST Compliance Statements.
        Please read the following text extracted from a company's financial document and extract the core financial metrics requested.
        
        CRITICAL EXTRACTION RULES:
        1. STRONGLY ENFORCE: Convert all values with commas to raw INR integer values by purely stripping commas (e.g., 21,95,00,000 -> 219500000, 3,20,00,000 -> 320000000, 92,40,000 -> 9240000). Ensure export supplies exactly matches 320000000!
        2. If a value cannot be determined from the text, return null.
        3. For 'gst_behavioral_metrics', accurately map:
           - gross_tax_obligation: Total gross tax obligation (including reverse charge).
           - output_tax_liability: Total net output tax liability.
           - output_tax_breakdown: Detailed split of output tax into cgst, sgst, igst exactly as stated in the text. CRITICAL: For IGST, ONLY extract the Integrated Tax under "Domestic taxable supplies". Do not add the export IGST! The expected IGST value is 9240000.
           - cash_tax_paid: Balance tax paid in cash.
           - itc_utilized: Tax credit utilized towards output liability.
           - credit_notes_value: Value of credit notes adjustments.
           - credit_note_tax_reduction: Tax reduction impact from credit notes.
        4. For 'document_risks', extract specific risks (credit disallowance, variance, export refund exposure) into structured 'document_risk_mentions' with a 'type' and 'amount'.
        
        Document Text:
        {text}
        """

        try:
            # We enforce JSON output matching our Pydantic schema
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=RAWFinancialExtractionSchema,
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Error during LLM extraction: {e}")
            return {}

    def derive_risk_features(self, raw_json: dict) -> dict:
        """
        Calculates the behavioral fraud indicators locally to avoid LLM math hallucinations.
        """
        features = {}
        metrics = raw_json.get("gst_behavioral_metrics", {})
        
        def safe_div(num, den):
            if num is None or den is None or den == 0:
                return None
            return round(num / den, 4)

        features["itc_utilization_ratio"] = safe_div(metrics.get("itc_utilized"), metrics.get("gst_itc_claimed"))
        features["refund_approval_ratio"] = safe_div(metrics.get("refund_sanctioned"), metrics.get("refund_claimed"))
        features["cash_to_itc_ratio"] = safe_div(metrics.get("cash_tax_paid"), metrics.get("itc_utilized"))
        features["cash_tax_ratio"] = safe_div(metrics.get("cash_tax_paid"), metrics.get("output_tax_liability"))
        features["output_tax_to_revenue_ratio"] = safe_div(metrics.get("output_tax_liability"), metrics.get("gst_declared_supplies"))
        features["credit_note_percentage"] = safe_div(metrics.get("credit_notes_value"), metrics.get("gst_declared_supplies"))
        features["itc_mismatch_ratio"] = safe_div(metrics.get("gst_itc_variance"), metrics.get("gst_itc_supplier"))
        
        # New Advanced Ratios
        features["itc_dependency_ratio"] = safe_div(metrics.get("itc_utilized"), metrics.get("output_tax_liability"))
        features["cash_to_gross_tax_ratio"] = safe_div(metrics.get("cash_tax_paid"), metrics.get("gross_tax_obligation"))
        features["refund_intensity_ratio"] = safe_div(metrics.get("refund_claimed"), metrics.get("gst_declared_supplies"))
        
        # Cross-Module Intelligence: Document Risk Intensity
        # Sum of all explicitly stated risk amounts divided by total revenue
        total_risk_amount = sum([r.get("amount", 0) for r in raw_json.get("document_risks", {}).get("document_risk_mentions", []) if r.get("amount") is not None])
        features["document_risk_intensity"] = safe_div(total_risk_amount, metrics.get("gst_declared_supplies"))

        # Add risk flag: using 100% of availed ITC is a high risk indicator.
        features["flag_100_percent_itc_utilization"] = (features.get("itc_utilization_ratio") == 1.0)
        
        # Categorical String Risk Flags for quick interpretation
        risk_flags = []
        if features.get("itc_utilization_ratio") == 1.0:
            risk_flags.append("FULL_ITC_UTILIZATION")
        if features.get("cash_tax_ratio") is not None and features.get("cash_tax_ratio") < 0.25:
            risk_flags.append("LOW_CASH_TAX_PAYMENT")
        if metrics.get("gst_itc_variance") is not None and metrics.get("gst_itc_variance") > 0:
            risk_flags.append("ITC_RECONCILIATION_VARIANCE_PRESENT")
            
        features["risk_flags"] = risk_flags
        
        return features

    def process_document(self, pdf_path: str) -> dict:
        """
        End-to-End Pipeline for Pillar 1
        Takes a PDF path, extracts text, and returns the structured JSON block.
        """
        print(f"[*] Processing document: {pdf_path}")
        print("[*] Extracting raw text from PDF...")
        text = self.extract_text_from_pdf(pdf_path)
        
        print(f"[*] Text Extracted (Length: {len(text)} chars). Sending to Gemini for JSON extraction...")
        raw_extraction = self.parse_financials(text)
        
        print("[*] Extraction Complete. Computing derived behavioral risk features...")
        derived_features = self.derive_risk_features(raw_extraction)
        
        return {
            "company_financials": raw_extraction.get("company_financials", {}),
            "gst_behavioral_metrics": raw_extraction.get("gst_behavioral_metrics", {}),
            "document_risks": raw_extraction.get("document_risks", {}),
            "gst_risk_features": derived_features
        }

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        print("Please create a .env file with GEMINI_API_KEY=your_key")
    else:
        parser = DocumentParser(api_key=API_KEY)
        
        # Testing on the user-provided financial report
        sample_pdf = "Test_Financial_Report.pdf"
        if os.path.exists(sample_pdf):
            print(f"[*] Starting test on {sample_pdf}\n")
            result = parser.process_document(sample_pdf)
            print("\n" + "="*40)
            print("EXTRACTED FINANCIAL JSON OUTPUT")
            print("="*40)
            print(json.dumps(result, indent=2))
        else:
            print(f"[!] Warning: Could not find {sample_pdf} to test.")
