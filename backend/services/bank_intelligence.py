from typing import Dict, Any, List
import pandas as pd
from services.session import IngestedDoc

def run_bank_intelligence(financials: Dict[str, Any], ingested_docs: List[IngestedDoc]) -> Dict[str, Any]:
    """
    Bank intelligence analysis.
    Works with LLM-extracted bank data from docs or financials.
    If full CSV is uploaded, deeper analysis is done.
    """
    # Look for extracted bank data in ingested docs
    bank_data = {}
    for doc in ingested_docs:
        if doc.doc_type == "BANK_STATEMENT" and hasattr(doc, "extracted_data"):
            bank_data = doc.extracted_data
            break
            
    total_inflow = float(bank_data.get("total_inflow", financials.get("total_inflow", 0.0)))
    total_outflow = float(bank_data.get("total_outflow", financials.get("total_outflow", 0.0)))
    
    cash_deposits = float(bank_data.get("cash_deposits", 0.0))
    
    cash_deposit_ratio = cash_deposits / total_inflow if total_inflow > 0 else 0.0
    
    # Heuristics for missing granular data
    round_tripping_score = 0.0
    if bank_data.get("high_frequency_transfers") == True:
        round_tripping_score = 0.6
        
    related_party_transfer_share = float(bank_data.get("related_party_outflows", 0.0)) / total_outflow if total_outflow > 0 else 0.0
    
    return {
        "bank_cash_deposit_ratio": float(cash_deposit_ratio),
        "bank_round_tripping_score": float(round_tripping_score),
        "bank_top_counterparty_share": None, # Null when per-supplier missing
        "bank_counterparty_hhi": None,
        "bank_related_party_transfer_share": float(related_party_transfer_share),
        "note": "Using extracted summary data. Counterparty metrics unavailable without full CSV/XLSX."
    }
