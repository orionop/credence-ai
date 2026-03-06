from typing import Dict, Any

def score_qualitative_notes(notes: str) -> Dict[str, Any]:
    """
    Direct port, works on text strings.
    """
    if not notes:
        return {
            "management_quality_score": 0.5,
            "capacity_utilization_penalty": 0.0,
            "qualitative_text_length": 0,
            "qualitative_positive_hits": 0,
            "qualitative_negative_hits": 0,
        }
        
    text = notes.lower()

    positive_terms = ["transparent", "strong management", "experienced", "conservative", "professional"]
    negative_terms = ["non-cooperative", "opaque", "poor controls", "mismanagement", "related party issues"]
    low_capacity_terms = ["low capacity", "40% capacity", "underutilized", "idle plant"]

    pos_hits = sum(text.count(t) for t in positive_terms)
    neg_hits = sum(text.count(t) for t in negative_terms)
    cap_hits = sum(text.count(t) for t in low_capacity_terms)

    # Management quality score between 0 and 1
    base = 0.5 + 0.1 * pos_hits - 0.1 * neg_hits
    management_quality_score = max(0.0, min(1.0, base))

    # Capacity utilization penalty between 0 and 1
    capacity_penalty = max(0.0, min(1.0, 0.2 * cap_hits))

    return {
        "management_quality_score": float(management_quality_score),
        "capacity_utilization_penalty": float(capacity_penalty),
        "qualitative_text_length": len(text),
        "qualitative_positive_hits": pos_hits,
        "qualitative_negative_hits": neg_hits,
    }
