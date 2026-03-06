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
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List
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


# Lazy-init to avoid import-time pydantic errors
_scoring_llm = None

def _get_scoring_llm():
    global _scoring_llm
    if _scoring_llm is None:
        from langchain_openai import ChatOpenAI
        _scoring_llm = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0).bind(
            response_format={"type": "json_object"}
        )
    return _scoring_llm

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
        from langchain_openai import ChatOpenAI
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


# ── Local Policy-Driven Scoring ─────────────────────────────────────────────

def load_risk_policy() -> Dict[str, Any]:
    """Load from backend/data/risk_policy.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    policy_path = os.path.join(base_dir, "data", "risk_policy.json")
    if not os.path.exists(policy_path):
        return {}
    with open(policy_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_effective_policy(sector: str) -> Dict[str, Any]:
    policy = load_risk_policy()
    sector = (sector or "").lower()
    sector_policies = policy.get("sector_policies", {})
    override = sector_policies.get(sector)
    if override:
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(policy.get(k), dict):
                merged = dict(policy[k])
                merged.update(v)
                policy[k] = merged
            else:
                policy[k] = v
    return policy

@dataclass
class RiskInputs:
    latest_revenue: float
    latest_ebitda: float
    latest_net_worth: float
    latest_total_debt: float
    bank_total_inflows: float
    bank_total_outflows: float
    litigation_risk_score: float = 0.0
    management_quality_score: float = 0.5
    capacity_utilization_penalty: float = 0.0
    cibil_risk_score: float = 0.0
    payroll_stability_score: float = 0.5
    related_party_risk_score: float = 0.0
    graph_risk_score: float = 0.0
    data_completeness_score: float = 0.0
    has_gst: bool = False
    has_bank: bool = False
    sanction_existing_debt: float = 0.0
    sanction_effective_rate: float = 0.0
    sanction_microfinance_exposure_flag: bool = False
    sanction_group_liability_flag: bool = False
    sanction_short_tenure_flag: bool = False
    sanction_high_interest_flag: bool = False
    news_sentiment_score: float = 0.0
    promoter_risk_score: float = 0.0
    research_litigation_news_count: float = 0.0
    research_sector_headwind_score: float = 0.0
    gst_anomaly_score: float = 0.0
    bank_anomaly_score: float = 0.0
    financials_found_flag: bool = False
    gst_itc_variance_ratio: float = 0.0
    gst_itc_top_supplier_share: float = 0.0
    gst_itc_dependency_ratio: float = 0.0
    gst_cash_tax_ratio: float = 0.0
    gst_reverse_charge_turnover_ratio: float = 0.0
    bank_cash_deposit_ratio: float = 0.0
    bank_round_tripping_score: float = 0.0
    bank_top_counterparty_share: float = 0.0
    bank_counterparty_hhi: float = 0.0
    bank_total_txn_volume: float = 0.0
    bank_related_party_transfer_share: float = 0.0

@dataclass
class RiskDecision:
    approve: bool
    recommended_limit: float
    recommended_rate: float
    score: float
    reasons: List[str]
    risk_band: str
    pd_estimate: float
    capacity_score: float
    character_score: float
    capital_score: float
    conditions_score: float
    collateral_score: float

def simple_rule_based_decision(features: RiskInputs, requested_limit: float, sector: str = None, base_rate: float = None) -> RiskDecision:
    reasons = []
    policy = get_effective_policy(sector)
    base_rate = base_rate if base_rate is not None else float(policy.get("base_rate", 10.0))

    capacity_score = 0.5
    character_score = 0.5
    capital_score = 0.5
    conditions_score = 0.5
    collateral_score = 0.5

    total_debt_for_leverage = features.latest_total_debt + features.sanction_existing_debt
    leverage = None
    revenue_to_limit = None
    if features.latest_net_worth > 0:
        leverage = (total_debt_for_leverage + requested_limit) / max(features.latest_net_worth, 1.0)
    if requested_limit > 0 and features.latest_revenue > 0:
        revenue_to_limit = features.latest_revenue / max(requested_limit, 1.0)
    
    lev_cfg = policy.get("leverage", {})
    rev_cfg = policy.get("revenue_to_limit", {})
    ebitda_cfg = policy.get("ebitda_margin", {})
    overlays = policy.get("overlays", {})

    lev_low = float(lev_cfg.get("low_threshold", 2.0))
    lev_med = float(lev_cfg.get("medium_threshold", 3.0))
    lev_w = lev_cfg.get("weights", {})
    if leverage is not None:
        if leverage <= lev_low:
            capital_score += float(lev_w.get("low", 0.4))
            reasons.append(f"Comfortable leverage (Debt/Net Worth <= {lev_low}x).")
        elif leverage <= lev_med:
            capital_score += float(lev_w.get("medium", 0.2))
            reasons.append(f"Moderate leverage (Debt/Net Worth between {lev_low}x and {lev_med}x).")
        else:
            capital_score += float(lev_w.get("high", -0.3))
            reasons.append(f"High leverage (Debt/Net Worth > {lev_med}x).")

    rev_high = float(rev_cfg.get("high_threshold", 4.0))
    rev_med = float(rev_cfg.get("medium_threshold", 2.0))
    rev_w = rev_cfg.get("weights", {})
    if revenue_to_limit is not None:
        if revenue_to_limit >= rev_high:
            capacity_score += float(rev_w.get("high", 0.3))
            reasons.append(f"Requested limit is conservative relative to revenue (Revenue / Limit >= {rev_high}x).")
        elif revenue_to_limit >= rev_med:
            capacity_score += float(rev_w.get("medium", 0.1))
            reasons.append(f"Requested limit is reasonable relative to revenue (Revenue / Limit between {rev_med}x and {rev_high}x).")
        else:
            capacity_score += float(rev_w.get("low", -0.2))
            reasons.append(f"Requested limit is aggressive relative to revenue (Revenue / Limit < {rev_med}x).")

    ebitda_high = float(ebitda_cfg.get("high_threshold", 0.15))
    ebitda_med = float(ebitda_cfg.get("medium_threshold", 0.08))
    ebitda_w = ebitda_cfg.get("weights", {})
    if features.latest_revenue > 0:
        ebitda_margin = features.latest_ebitda / max(features.latest_revenue, 1.0)
        if ebitda_margin >= ebitda_high:
            capacity_score += float(ebitda_w.get("high", 0.2))
            reasons.append(f"Healthy EBITDA margin (>= {ebitda_high:.0%}).")
        elif ebitda_margin >= ebitda_med:
            capacity_score += float(ebitda_w.get("medium", 0.05))
            reasons.append(f"Acceptable EBITDA margin ({ebitda_med:.0%}–{ebitda_high:.0%}).")
        else:
            capacity_score += float(ebitda_w.get("low", -0.15))
            reasons.append(f"Thin EBITDA margin (< {ebitda_med:.0%}).")

    if features.management_quality_score >= 0.7:
        character_score += float(overlays.get("management_quality", 0.1))
    elif features.management_quality_score <= 0.3:
        character_score += float(overlays.get("management_concern", -0.1))

    if features.capacity_utilization_penalty > 0.0:
        capacity_score += float(overlays.get("capacity_penalty_base", -0.05)) * (1.0 + features.capacity_utilization_penalty)

    if features.cibil_risk_score > 0.0:
        character_score += float(overlays.get("cibil_factor", -0.2)) * features.cibil_risk_score
    if features.litigation_risk_score > 0.0:
        character_score += float(overlays.get("litigation_factor", -0.15)) * features.litigation_risk_score
    if features.related_party_risk_score > 0.0:
        character_score += float(overlays.get("related_party_factor", -0.1)) * features.related_party_risk_score
    if features.graph_risk_score > 0.0:
        character_score += float(overlays.get("graph_factor", -0.15)) * features.graph_risk_score

    # Payroll stability
    if features.payroll_stability_score >= 0.7:
        capacity_score += float(overlays.get("payroll_positive", 0.05))
    elif features.payroll_stability_score <= 0.3:
        capacity_score += float(overlays.get("payroll_negative", -0.05))

    # Sanction letter flags
    if features.sanction_microfinance_exposure_flag:
        conditions_score += float(overlays.get("microfinance_exposure_factor", -0.05))
    if features.sanction_group_liability_flag:
        conditions_score += float(overlays.get("group_liability_factor", -0.03))
    if features.sanction_short_tenure_flag:
        conditions_score += float(overlays.get("short_tenure_factor", -0.02))
    if features.sanction_high_interest_flag:
        conditions_score += float(overlays.get("high_interest_factor", -0.05))

    # News sentiment & promoter risk (from research agent)
    if features.news_sentiment_score > 0.0:
        conditions_score += float(overlays.get("news_sentiment_factor", 0.05)) * features.news_sentiment_score
    if features.promoter_risk_score > 0.0:
        character_score += float(overlays.get("promoter_risk_factor", -0.05)) * features.promoter_risk_score
    if features.research_sector_headwind_score > 0.0:
        conditions_score += float(overlays.get("sector_headwind_factor", -0.05)) * features.research_sector_headwind_score

    # GST & Bank anomaly scores (from z-score detector)
    if features.gst_anomaly_score > 0.0:
        conditions_score += float(overlays.get("gst_anomaly_factor", -0.05)) * features.gst_anomaly_score
    if features.bank_anomaly_score > 0.0:
        conditions_score += float(overlays.get("bank_anomaly_factor", -0.05)) * features.bank_anomaly_score

    if features.gst_itc_variance_ratio > 0.0:
        conditions_score -= min(0.08, features.gst_itc_variance_ratio * 0.08)
    if features.gst_itc_dependency_ratio > 0.9:
        conditions_score -= 0.03
    if features.gst_cash_tax_ratio > 0.0 and features.gst_cash_tax_ratio < 0.15:
        conditions_score -= 0.02
    if features.bank_round_tripping_score > 0.3:
        conditions_score -= 0.04

    def _clamp(x: float) -> float:
        return max(0.0, min(1.0, x))

    capacity_score = _clamp(capacity_score)
    character_score = _clamp(character_score)
    capital_score = _clamp(capital_score)
    conditions_score = _clamp(conditions_score)
    collateral_score = _clamp(collateral_score)

    five_c_weights = policy.get("five_c_weights", {})
    w_capacity = float(five_c_weights.get("capacity", 0.3))
    w_character = float(five_c_weights.get("character", 0.25))
    w_capital = float(five_c_weights.get("capital", 0.2))
    w_conditions = float(five_c_weights.get("conditions", 0.15))
    w_collateral = float(five_c_weights.get("collateral", 0.1))

    normalized_score = (
        capacity_score * w_capacity
        + character_score * w_character
        + capital_score * w_capital
        + conditions_score * w_conditions
        + collateral_score * w_collateral
    )

    approve = normalized_score >= 0.5
    recommended_limit = requested_limit * (1.1 if normalized_score >= 0.75 else 1.0 if normalized_score >= 0.6 else 0.8) if approve else 0.0

    bands = policy.get("spread_bands", {})
    strong_min = float(bands.get("strong_min", 0.75))
    moderate_min = float(bands.get("moderate_min", 0.6))
    borderline_min = float(bands.get("borderline_min", 0.5))
    spreads_cfg = bands.get("spreads", {})
    
    if normalized_score >= strong_min:
        spread = float(spreads_cfg.get("strong", 1.0))
        risk_band, pd_estimate = "LOW", 0.01
    elif normalized_score >= moderate_min:
        spread = float(spreads_cfg.get("moderate", 2.0))
        risk_band, pd_estimate = "MEDIUM", 0.05
    elif normalized_score >= borderline_min:
        spread = float(spreads_cfg.get("borderline", 3.0))
        risk_band, pd_estimate = "ELEVATED", 0.10
    else:
        spread, risk_band, pd_estimate = 0.0, "HIGH", 0.2

    recommended_rate = base_rate + spread if approve else 0.0

    return RiskDecision(
        approve=approve, recommended_limit=recommended_limit, recommended_rate=recommended_rate,
        score=normalized_score, reasons=reasons, risk_band=risk_band, pd_estimate=pd_estimate,
        capacity_score=capacity_score, character_score=character_score, capital_score=capital_score,
        conditions_score=conditions_score, collateral_score=collateral_score
    )

def compute_local_risk_decision(
    financials: Dict[str, Any], 
    rich_gst_data: Dict[str, Any], 
    sector: str, 
    requested_limit: str,
    gst_reconciliation: Dict[str, Any] = None,
    bank_intelligence: Dict[str, Any] = None,
    graph_analysis: Dict[str, Any] = None,
    advanced_credit: Dict[str, Any] = None,
    qualitative_scores: Dict[str, Any] = None,
    z_score_anomalies: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Compute risk decision using local rule-based engine.
    """
    gst = gst_reconciliation or {}
    bank = bank_intelligence or {}
    graph = graph_analysis or {}
    adv = advanced_credit or {}
    qual = qualitative_scores or {}
    z_anom = z_score_anomalies or {}
    
    try:
        clean_amt = "".join(filter(str.isdigit, str(requested_limit)))
        req_limit_float = float(clean_amt) if clean_amt else 10000000.0  # default 10M
    except ValueError:
        req_limit_float = 10000000.0

    # Build RiskInputs — wire every feature from its source module
    inputs = RiskInputs(
        latest_revenue=float(financials.get("latest_revenue", 0.0)),
        latest_ebitda=float(financials.get("latest_ebitda", 0.0)),
        latest_net_worth=float(financials.get("latest_net_worth", 0.0)),
        latest_total_debt=float(financials.get("latest_total_debt", 0.0)),
        bank_total_inflows=float(financials.get("total_inflow", 0.0)),
        bank_total_outflows=float(financials.get("total_outflow", 0.0)),
        
        # From qualitative module
        litigation_risk_score=float(financials.get("litigation_risk_score", 0.0)),
        management_quality_score=float(qual.get("management_quality_score", 0.5)),
        capacity_utilization_penalty=float(qual.get("capacity_utilization_penalty", 0.0)),
        
        # From advanced_credit module
        cibil_risk_score=float(adv.get("cibil_risk_score", 0.0)),
        payroll_stability_score=float(financials.get("payroll_stability_score", 0.5)),
        related_party_risk_score=float(adv.get("related_party_risk_score", 0.0)),
        
        # From graph analysis module
        graph_risk_score=float(graph.get("graph_risk_score", 0.0)),
        
        has_gst=bool(gst),
        has_bank=bool(bank),
        
        # Sanction letter features (from financials, populated by ingestor.extract_sanction_features)
        sanction_existing_debt=float(financials.get("sanction_existing_debt", 0.0)),
        sanction_effective_rate=float(financials.get("sanction_effective_rate", 0.0)),
        sanction_microfinance_exposure_flag=bool(financials.get("sanction_microfinance_exposure_flag", False)),
        sanction_group_liability_flag=bool(financials.get("sanction_group_liability_flag", False)),
        sanction_short_tenure_flag=bool(financials.get("sanction_short_tenure_flag", False)),
        sanction_high_interest_flag=bool(financials.get("sanction_high_interest_flag", False)),
        
        # From research agent (surfaced via financials or research)
        news_sentiment_score=float(financials.get("news_sentiment_score", 0.0)),
        promoter_risk_score=float(financials.get("promoter_risk_score", 0.0)),
        research_litigation_news_count=float(financials.get("research_litigation_news_count", 0.0)),
        research_sector_headwind_score=float(financials.get("research_sector_headwind_score", 0.0)),
        
        # From z-score anomaly detector
        gst_anomaly_score=float(z_anom.get("gst_anomaly_score", gst.get("gst_anomaly_score", 0.0))),
        bank_anomaly_score=float(z_anom.get("bank_anomaly_score", bank.get("bank_anomaly_score", 0.0))),
        
        # GST reconciliation features
        gst_itc_variance_ratio=float(gst.get("gst_itc_variance_ratio", 0.0)),
        gst_itc_top_supplier_share=float(gst.get("gst_itc_top_supplier_share", 0.0) or 0.0),
        gst_itc_dependency_ratio=float(gst.get("gst_itc_dependency_ratio", 0.0)),
        gst_cash_tax_ratio=float(gst.get("gst_cash_tax_ratio", 0.0)),
        gst_reverse_charge_turnover_ratio=float(gst.get("gst_reverse_charge_turnover_ratio", 0.0)),
        
        # Bank intelligence features
        bank_cash_deposit_ratio=float(bank.get("bank_cash_deposit_ratio", 0.0)),
        bank_round_tripping_score=float(bank.get("bank_round_tripping_score", 0.0)),
        bank_top_counterparty_share=float(bank.get("bank_top_counterparty_share", 0.0) or 0.0),
        bank_related_party_transfer_share=float(bank.get("bank_related_party_transfer_share", 0.0)),
    )
    
    decision = simple_rule_based_decision(inputs, req_limit_float, sector)
    
    return {
        "approve": decision.approve,
        "recommended_limit": decision.recommended_limit,
        "recommended_rate": decision.recommended_rate,
        "score": decision.score,
        "reasons": decision.reasons,
        "risk_band": decision.risk_band,
        "pd_estimate": decision.pd_estimate,
        "capacity_score": decision.capacity_score,
        "character_score": decision.character_score,
        "capital_score": decision.capital_score,
        "conditions_score": decision.conditions_score,
        "collateral_score": decision.collateral_score,
    }
