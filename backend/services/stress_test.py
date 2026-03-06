from typing import List, Dict, Any
import copy

def run_stress_tests(
    financials: Dict[str, Any],
    rich_gst_data: Dict[str, Any],
    sector: str,
    requested_limit: float,
    base_decision: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Runs stress scenarios on the base decision by adjusting key financials.
    In a full implementation, this would re-run the compute_local_risk_decision engine.
    For this integration, we simulate the output based on the base_decision.
    """
    scenarios = []
    
    # helper to degrade score and band
    def _apply_stress(name: str, score_drop: float, rate_increase: float, limit_multiplier: float) -> Dict[str, Any]:
        base_score = float(base_decision.get("score", 0.0))
        new_score = max(0.0, base_score - score_drop)
        
        base_rate = float(base_decision.get("recommended_rate", 12.0))
        new_rate = base_rate + rate_increase
        
        base_limit = float(base_decision.get("recommended_limit", requested_limit))
        new_limit = base_limit * limit_multiplier
        
        # simple banding
        if new_score >= 0.7:
            band = "Low Risk"
        elif new_score >= 0.5:
            band = "Medium Risk"
        else:
            band = "High Risk"
            
        return {
            "name": name,
            "score": float(new_score),
            "risk_band": band,
            "recommended_limit": float(new_limit),
            "recommended_rate": float(new_rate)
        }

    # Scenario 1: Revenue -20%
    scenarios.append(_apply_stress("Revenue -20%", 0.05, 0.5, 0.8))

    # Scenario 2: EBITDA -30%
    scenarios.append(_apply_stress("EBITDA -30%", 0.08, 0.75, 0.7))

    # Scenario 3: Elevated anomalies
    scenarios.append(_apply_stress("Elevated Anomalies", 0.1, 1.0, 0.6))
    
    # Scenario 4: Rate +200bps (cost of capital stress)
    scenarios.append(_apply_stress("Rate +200bps", 0.02, 2.0, 0.9))
    
    # Scenario 5: Combined stress
    scenarios.append(_apply_stress("Combined Stress", 0.2, 3.0, 0.5))

    return scenarios
