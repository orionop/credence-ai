from typing import Dict, Any

def run_gst_reconciliation(rich_gst_data: Dict[str, Any], financials: Dict[str, Any]) -> Dict[str, Any]:
    """
    GST reconciliation using structured data from Gemini extraction.
    Computes variance and dependency ratios.
    """
    if not rich_gst_data:
        return {}
        
    metrics = rich_gst_data.get("gst_behavioral_cash_metrics", {})
    
    itc_2a_total = float(metrics.get("itc_2a_total", 0.0))
    itc_3b_total = float(metrics.get("itc_3b_total", 0.0))
    
    itc_variance = itc_3b_total - itc_2a_total
    itc_variance_ratio = abs(itc_variance) / max(itc_3b_total, 1.0)
    
    output_tax_total = float(metrics.get("output_tax_liability", 0.0))
    cash_tax_total = float(metrics.get("cash_tax_paid", 0.0))
    
    def _safe_div(num: float, den: float) -> float:
        return float(num) / float(den) if den > 0 else 0.0

    itc_dependency_ratio = _safe_div(itc_3b_total, output_tax_total)
    cash_tax_ratio = _safe_div(cash_tax_total, output_tax_total)
    
    refund_claimed = float(metrics.get("refund_claimed", 0.0))
    declared_supplies = float(metrics.get("declared_supplies", max(financials.get("latest_revenue", 0.0), 0.0)))
    
    refund_intensity_ratio = _safe_div(refund_claimed, declared_supplies)
    
    reverse_charge = float(metrics.get("reverse_charge_turnover", 0.0))
    reverse_charge_ratio = _safe_div(reverse_charge, declared_supplies)
    
    return {
        "gst_itc_total_2a": itc_2a_total,
        "gst_itc_total_3b": itc_3b_total,
        "gst_itc_variance": float(itc_variance),
        "gst_itc_variance_ratio": float(itc_variance_ratio),
        "gst_itc_dependency_ratio": float(itc_dependency_ratio),
        "gst_cash_tax_ratio": float(cash_tax_ratio),
        "gst_refund_intensity_ratio": float(refund_intensity_ratio),
        "gst_reverse_charge_turnover_ratio": float(reverse_charge_ratio),
        "gst_itc_top_supplier_share": None,
        "gst_itc_hhi": None,
        "note": "Supplier concentration returns null when per-supplier data unavailable"
    }
