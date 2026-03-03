from services.scoring import assign_risk_tier, compute_sanction_limit, pd_to_corporate_score

def test_risk_tiers():
    print("Testing Risk Tiers...")
    # AAA Tier
    rating, rec, premium = assign_risk_tier(0.01)
    assert rating == "AAA"
    assert rec == "approved"
    
    # BBB Tier
    rating, rec, premium = assign_risk_tier(0.30)
    assert rating == "BBB"
    assert rec == "conditional"
    
    # Rejected
    rating, rec, premium = assign_risk_tier(0.60)
    assert rating == "B/CCC"
    assert rec == "rejected"
    print("Risk Tier Test PASSED")

def test_sanction_logic():
    print("Testing Sanction Logic...")
    # AAA should get 100%
    limit = compute_sanction_limit(50.0, "AAA")
    assert limit == "₹50.00 Cr"
    
    # BBB should get 55%
    limit = compute_sanction_limit(10.0, "BBB")
    assert limit == "₹5.50 Cr"
    
    # BB should get 0%
    limit = compute_sanction_limit(10.0, "BB")
    assert limit == "₹0.00 Cr"
    print("Sanction Logic Test PASSED")

def test_score_conversion():
    print("Testing Score Conversion...")
    score_low_pd = pd_to_corporate_score(0.01)
    score_high_pd = pd_to_corporate_score(0.50)
    assert score_low_pd > score_high_pd
    assert 300 <= score_low_pd <= 900
    print(f"Scores: Low PD={score_low_pd}, High PD={score_high_pd}")
    print("Score Conversion Test PASSED")

if __name__ == "__main__":
    test_risk_tiers()
    test_sanction_logic()
    test_score_conversion()
