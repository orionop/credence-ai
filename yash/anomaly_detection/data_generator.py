import pandas as pd
import numpy as np
import os

def generate_mock_financial_data(output_dir="data/mock"):
    """
    Generates realistic mock dataset for 50 companies over 12 months.
    It simulates GSTR-3B (Declared Sales), GSTR-2A (Supplier Input Tax Credit),
    and Bank Statement inflow/outflow to train our Isolation Forest.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    np.random.seed(42)
    companies = [f"COMP_{i}" for i in range(1, 51)]
    months = pd.date_range(start="2024-01-01", periods=12, freq="M").strftime("%Y-%m").tolist()
    
    data = []
    
    for comp in companies:
        # 10% of companies are "fraudulent" (Circular Trading / Revenue Inflation)
        is_fraud = np.random.rand() > 0.90
        
        base_revenue = np.random.randint(5000000, 50000000)
        
        for month in months:
            # Normal behavior: GSTR-3B (Declared) closely matches GSTR-2A (Supplier claims)
            gstr_3b = base_revenue * (1 + np.random.normal(0, 0.05))
            gstr_2a = gstr_3b * (1 - np.random.uniform(0.01, 0.05))
            
            # Normal Bank flows align with revenue
            bank_inflow = gstr_3b * (1 + np.random.normal(0, 0.02))
            bank_outflow = gstr_3b * (0.8 + np.random.normal(0, 0.05))
            
            if is_fraud:
                # FRAUD PATTERN 1: Circular Trading
                # Massive spikes in bank inflow/outflow that perfectly match (money spinning)
                # while actual GST declared (3B) remains low or completely mismatched to 2A.
                fraud_multiplier = np.random.uniform(3.0, 8.0)
                bank_inflow *= fraud_multiplier
                bank_outflow *= fraud_multiplier 
                
                # FRAUD PATTERN 2: Revenue Inflation (Fake ITC)
                # Claiming massive ITC in 3B while supplier 2A is very low.
                gstr_3b *= np.random.uniform(1.5, 3.0)
                gstr_2a *= 0.3
                
            data.append({
                "Company_ID": comp,
                "Month": month,
                "GSTR_3B_Declared": round(gstr_3b, 2),
                "GSTR_2A_Supplier_ITC": round(gstr_2a, 2),
                "Bank_Inflow": round(bank_inflow, 2),
                "Bank_Outflow": round(bank_outflow, 2),
                "Is_Fraudulent_Flag": is_fraud # ground truth for testing/validation
            })

    df = pd.DataFrame(data)
    
    # Feature Engineering (This is what the Isolation Forest will see)
    df['GSTR_Mismatch_Ratio'] = abs(df['GSTR_3B_Declared'] - df['GSTR_2A_Supplier_ITC']) / df['GSTR_3B_Declared']
    df['Bank_vs_GST_Ratio'] = df['Bank_Inflow'] / df['GSTR_3B_Declared']
    df['Velocity_Ratio'] = df['Bank_Inflow'] / (df['Bank_Outflow'] + 1) # Close to 1 in circular trading
    
    output_path = os.path.join(output_dir, "gst_bank_mock_data.csv")
    df.to_csv(output_path, index=False)
    print(f"[*] Generated {len(df)} rows of mock financial data at {output_path}")

if __name__ == "__main__":
    generate_mock_financial_data()
