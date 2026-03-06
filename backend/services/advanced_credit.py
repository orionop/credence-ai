from typing import Dict, Any

def analyze_cibil_from_extracted(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Keyword-based CIBIL risk scoring adapted for credence-ai's structured extraction.
    """
    if not extracted_data:
        return {
            "cibil_risk_score": 0.0,
            "cibil_high_risk_hits": 0,
            "cibil_dpd_hits": 0,
        }
        
    # extracted_data could be text output from research or specific keys
    text = str(extracted_data).lower()
    
    high_risk_terms = ["write-off", "settled", "wilful defaulter", "loss", "doubtful"]
    dpd_terms = ["30+ dpd", "60+ dpd", "90+ dpd", "dpd"]

    high_risk_hits = sum(text.count(t) for t in high_risk_terms)
    dpd_hits = sum(text.count(t) for t in dpd_terms)

    cibil_risk_score = max(0.0, min(1.0, (high_risk_hits + dpd_hits) / 10.0)) if (high_risk_hits + dpd_hits) > 0 else 0.0

    return {
        "cibil_risk_score": float(cibil_risk_score),
        "cibil_high_risk_hits": high_risk_hits,
        "cibil_dpd_hits": dpd_hits,
    }


def analyze_related_party(bank_intelligence: Dict[str, Any], financials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze related party risk from bank intelligence and financials.
    """
    related_party_share = float(bank_intelligence.get("bank_related_party_transfer_share", 0.0))
    total_volume = float(bank_intelligence.get("bank_total_txn_volume", financials.get("total_outflow", 0.0)))
    
    related_party_risk_score = max(0.0, min(1.0, related_party_share * 2.0))

    return {
        "related_party_risk_score": float(related_party_risk_score),
        "related_party_total_volume": float(total_volume * related_party_share),
        "related_party_top_share": float(related_party_share),
    }
