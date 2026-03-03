"""
Five Cs Scoring Engine for Corporate Credit.
Uses GPT for Five Cs evaluation + deterministic risk tier assignment
based on PD-driven tier/score framework.

Key features:
- Risk tier bins (AAA to B/CCC) based on Probability of Default
- PD → CIBIL-scale score conversion (logit transform to 300-900 scale)
- Sanction percentage by risk tier
- Explainable score decomposition
"""

import logging
import json
import numpy as np
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Risk Tier Framework ─────────────────────────────────────────────────────

CORPORATE_RISK_TIERS = [
    (0.00, 0.02, "AAA",  "approved",    "0.75%"),
    (0.02, 0.05, "AA+",  "approved",    "1.25%"),
    (0.05, 0.08, "AA",   "approved",    "1.75%"),
    (0.08, 0.12, "A+",   "approved",    "2.25%"),
    (0.12, 0.18, "A",    "conditional", "2.75%"),
    (0.18, 0.25, "BBB+", "conditional", "3.50%"),
    (0.25, 0.35, "BBB",  "conditional", "4.50%"),
    (0.35, 0.50, "BB",   "rejected",    "6.00%"),
    (0.50, 1.00, "B/CCC","rejected",    "8.00%"),
]

SANCTION_PCT_BY_RATING = {
    "AAA": 1.00, "AA+": 0.95, "AA": 0.90, "A+": 0.85, "A": 0.80,
    "BBB+": 0.70, "BBB": 0.55, "BB": 0.0, "B/CCC": 0.0
}

RECOVERY_RATING_MAP = {
    "AAA": "Superior (RR1)", "AA+": "Superior (RR1)", "AA": "Strong (RR2)",
    "A+": "Strong (RR2)", "A": "Good (RR3)", "BBB+": "Good (RR3)",
    "BBB": "Average (RR4)", "BB": "Below Average (RR5)", "B/CCC": "Poor (RR6)"
}

# Feature explanations for corporate credit context
FEATURE_EXPLANATIONS = {
    "revenue_yoy_growth": "Revenue growth trajectory indicates business momentum and market acceptance.",
    "ebitda_margin": "EBITDA margin reflects operational efficiency and pricing power.",
    "debt_to_equity": "Debt-to-equity ratio shows leverage and financial risk tolerance.",
    "current_ratio": "Current ratio indicates short-term liquidity and working capital adequacy.",
    "interest_coverage": "Interest coverage ratio shows ability to service debt obligations.",
    "promoter_holding": "Promoter holding percentage indicates management commitment and skin-in-the-game.",
    "dscr": "Debt Service Coverage Ratio shows cash flow adequacy relative to debt commitments.",
    "litigation_risk": "Active litigation exposure could impair financial stability and reputation.",
    "sector_outlook": "Industry-level risks and regulatory headwinds affecting future prospects.",
    "management_quality": "Track record, governance practices, and strategic clarity of leadership.",
}


def pd_to_corporate_score(pd_value: float, scale_min: int = 300, scale_max: int = 900) -> float:
    """Convert Probability of Default to a CIBIL-like commercial score (300-900).
    Uses logit transform to convert PD to a CIBIL-scale score."""
    p = np.clip(pd_value, 1e-6, 1 - 1e-6)
    x = -np.log(p / (1 - p))
    x_norm = np.clip((x - (-6)) / (6 - (-6)), 0, 1)
    score = scale_min + (scale_max - scale_min) * x_norm
    return round(float(score), 1)


def score_to_normalized(score: float, scale_min: int = 300, scale_max: int = 900) -> int:
    """Convert CIBIL-like score to 0-100 normalized score."""
    return int(np.clip((score - scale_min) / (scale_max - scale_min) * 100, 0, 100))


def assign_risk_tier(pd_value: float) -> tuple:
    """Assign corporate rating, recommendation, and risk premium based on PD.
    Maps PD to a standardized risk tier."""
    for lo, hi, rating, rec, premium in CORPORATE_RISK_TIERS:
        if lo <= pd_value < hi:
            return rating, rec, premium
    return "B/CCC", "rejected", "8.00%"


def compute_sanction_limit(requested_cr: float, rating: str) -> str:
    """Compute recommended credit limit based on risk tier.
    Determines facility sanction percentage based on risk tier."""
    pct = SANCTION_PCT_BY_RATING.get(rating, 0.0)
    limit = requested_cr * pct
    return f"₹{limit:.2f} Cr"


# ── LLM-based Five Cs Scoring ───────────────────────────────────────────────

llm = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0).bind(
    response_format={"type": "json_object"}
)

SCORING_PROMPT = """
You are an expert Indian corporate credit analyst at an institutional bank (e.g. SBI, HDFC, ICICI).
Evaluate the following entity using the "Five Cs of Credit" framework.

**Borrower Context**:
- **Sector**: {sector}
- **Requested Facility Amount**: {loan_amount}

**Entity Financials (extracted from filings or GST):**
{financials}

**Secondary Research Insights (web crawl):**
{insights}

**Primary Field Notes (from credit officer due diligence):**
{primary_notes}

Return a JSON object with this EXACT structure:
{{
  "character": {{
    "score": <0-100>,
    "summary": "<1 line description>",
    "detail": "<2-3 sentence AI explanation with specific data points>",
    "key_factors": ["<factor 1>", "<factor 2>"]
  }},
  "capacity": {{
    "score": <0-100>,
    "summary": "<1 line description>",
    "detail": "<2-3 sentence AI explanation with specific data points>",
    "key_factors": ["<factor 1>", "<factor 2>"]
  }},
  "capital": {{
    "score": <0-100>,
    "summary": "<1 line description>",
    "detail": "<2-3 sentence AI explanation with specific data points>",
    "key_factors": ["<factor 1>", "<factor 2>"]
  }},
  "collateral": {{
    "score": <0-100>,
    "summary": "<1 line description>",
    "detail": "<2-3 sentence AI explanation with specific data points>",
    "key_factors": ["<factor 1>", "<factor 2>"]
  }},
  "conditions": {{
    "score": <0-100>,
    "summary": "<1 line description>",
    "detail": "<2-3 sentence AI explanation with specific data points>",
    "key_factors": ["<factor 1>", "<factor 2>"]
  }},
  "probability_of_default_numeric": <0.0 to 1.0 as a decimal>,
  "requested_limit_cr": <estimated sensible limit in Crores as a number>,
  "appraisal_summary": "<2-3 sentence professional summary for the CAM>"
}}

Score based on Indian banking standards. Consider DSCR, D/E ratio, EBITDA margins,
litigation risk, promoter track record, collateral coverage, sector headwinds,
and RBI regulatory environment. Be specific and data-driven.

IMPORTANT: probability_of_default_numeric MUST be a decimal between 0.0 and 1.0
(e.g. 0.08 for 8% PD). requested_limit_cr should be a number (e.g. 12.5 for ₹12.5 Cr).
"""

def compute_five_cs(
    financials: dict,
    research_insights: list,
    primary_notes: str = "",
    loan_amount: str = "Not Specified",
    sector: str = "Unknown",
    rich_gst_data: dict = None
) -> dict:
    """
    Compute Five Cs scores using LLM analysis + deterministic risk framework.
    Combines AI-generated Five Cs evaluation with deterministic
    PD→tier→sanction pipeline for objective decision logic.
    """
    logger.info(f"Computing professional-grade Five Cs for loan: {loan_amount}...")

    try:
        # Use GPT-4 for professional-grade analysis in 'Real Product' mode
        llm_engine = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.1).bind(
            response_format={"type": "json_object"}
        )
        logger.info("Using GPT-4 Turbo for institutional appraisal")

        financials_str = json.dumps(financials, indent=2) if financials else "No financials available yet."
        insights_str = "\n".join([
            f"- {i.get('title', i) if isinstance(i, dict) else i}"
            for i in research_insights
        ]) if research_insights else "No research insights available yet."
        
        # Add Anomaly Data if available
        anomaly_str = "No specific anomaly detection run."
        if rich_gst_data and "gst_risk_features" in rich_gst_data:
            riskf = rich_gst_data["gst_risk_features"]
            if "anomaly_detection" in riskf:
                ad = riskf["anomaly_detection"]
                anomaly_str = f"Mathematical Anomaly Risk Score: {ad.get('anomaly_risk_score')}% ({ad.get('risk_level')}). Flags: {', '.join(riskf.get('risk_flags', []))}"

        formatted_prompt = SCORING_PROMPT + f"\n\n**Special Mathematical Anomaly Detection Data**:\n{anomaly_str}"
        formatted_prompt = formatted_prompt.format(
            financials=financials_str,
            insights=insights_str,
            primary_notes=primary_notes if primary_notes else "None provided.",
            loan_amount=loan_amount,
            sector=sector
        )

        response = llm_engine.invoke([HumanMessage(content=formatted_prompt)])
        scores = json.loads(response.content)

        # ── Deterministic Risk Framework ─────────────────────────────────
        pd_numeric = float(scores.get("probability_of_default_numeric", 0.15))
        
        # Parse loan amount to numeric if possible (e.g. "₹5,00,00,000" -> 5 Cr)
        requested_cr = 10.0
        try:
            clean_amt = "".join(filter(str.isdigit, loan_amount))
            if clean_amt:
                val = float(clean_amt)
                # 1 Cr = 1,00,00,000. If val is large, convert. 
                # If val is small (e.g. 50), it might already be in Cr or lakhs.
                # Heuristic: if > 1000, assume raw INR.
                if val > 1000:
                    requested_cr = val / 10_000_000
                else:
                    requested_cr = val
        except:
            requested_cr = float(scores.get("requested_limit_cr", 10.0))

        # Assign risk tier based on PD
        credit_rating, recommendation, risk_premium = assign_risk_tier(pd_numeric)

        # Convert PD to CIBIL-like score
        commercial_score = pd_to_corporate_score(pd_numeric)
        overall_score = score_to_normalized(commercial_score)

        # Compute sanction limit
        recommended_limit = compute_sanction_limit(requested_cr, credit_rating)

        # Recovery rating
        recovery_rating = RECOVERY_RATING_MAP.get(credit_rating, "Average (RR4)")

        # LGD estimation
        lgd_map = {"Superior (RR1)": "5-10%", "Strong (RR2)": "10-20%",
                    "Good (RR3)": "20-30%", "Average (RR4)": "30-45%",
                    "Below Average (RR5)": "45-60%", "Poor (RR6)": "60-80%"}
        loss_given_default = lgd_map.get(recovery_rating, "30-45%")

        # Enrich the response
        scores["overall_score"] = overall_score
        scores["credit_rating"] = credit_rating
        scores["probability_of_default"] = f"{pd_numeric * 100:.1f}%"
        scores["loss_given_default"] = loss_given_default
        scores["recovery_rating"] = recovery_rating
        scores["recommendation"] = recommendation
        scores["recommended_limit"] = recommended_limit
        scores["risk_premium"] = risk_premium
        scores["commercial_score"] = commercial_score  # 300-900 CIBIL-like

        logger.info(f"Professional scoring complete. Rating: {credit_rating}, PD: {pd_numeric:.2%}, Score: {overall_score}/100")
        return scores

    except Exception as e:
        logger.error(f"Error computing Five Cs: {e}")
        # Fallback with reasonable defaults
        return {
            "character": {"score": 65, "summary": "Moderate risk profile", "detail": f"Scoring not available: {str(e)}", "key_factors": []},
            "capacity": {"score": 70, "summary": "Adequate cash flow coverage", "detail": f"Scoring not available: {str(e)}", "key_factors": []},
            "capital": {"score": 55, "summary": "Leveraged capital structure", "detail": f"Scoring not available: {str(e)}", "key_factors": []},
            "collateral": {"score": 75, "summary": "Adequate security coverage", "detail": f"Scoring not available: {str(e)}", "key_factors": []},
            "conditions": {"score": 50, "summary": "Mixed sector outlook", "detail": f"Scoring not available: {str(e)}", "key_factors": []},
            "overall_score": 63,
            "credit_rating": "BBB",
            "probability_of_default": "3.8%",
            "loss_given_default": "30-45%",
            "recovery_rating": "Average (RR4)",
            "recommendation": "conditional",
            "recommended_limit": "₹8.00 Cr",
            "risk_premium": "3.5%",
            "commercial_score": 625.0,
            "appraisal_summary": "Entity shows moderate credit profile. Full scoring unavailable due to API error."
        }
