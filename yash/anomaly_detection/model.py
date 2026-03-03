import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import os

class FinancialAnomalyDetector:
    def __init__(self, model_path="models/isolation_forest.pkl"):
        self.model_path = model_path
        # Hyperparameters tuned for ~10% expected fraud rate
        self.model = IsolationForest(n_estimators=100, contamination=0.10, random_state=42)
        
        # The key features engineered from GST and Bank Statements
        self.features = ['GSTR_Mismatch_Ratio', 'Bank_vs_GST_Ratio', 'Velocity_Ratio']

    def train(self, data_path: str):
        """
        Trains the Isolation Forest on the historical mock data to learn what
        normal Indian corporate financial flows look like.
        """
        print(f"[*] Training Anomaly Detector on {data_path}...")
        df = pd.read_csv(data_path)
        
        X = df[self.features].fillna(0)
        
        self.model.fit(X)
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        print(f"[*] Model saved to {self.model_path}")

    def predict(self, company_data: pd.DataFrame) -> dict:
        """
        Takes a new company's data (12 months of GST/Bank flows),
        runs anomaly detection, and returns a grouped risk score.
        """
        if not os.path.exists(self.model_path):
            raise FileNotFoundError("Model not trained yet.")
            
        model = joblib.load(self.model_path)
        X = company_data[self.features].fillna(0)
        
        # Isolation Forest returns 1 for normal, -1 for anomaly
        predictions = model.predict(X)
        
        # Calculate how many of the 12 months were flagged as anomalous
        anomaly_count = sum(predictions == -1)
        total_months = len(predictions)
        
        risk_score = round((anomaly_count / total_months) * 100, 2)
        
        risk_level = "LOW"
        if risk_score > 50:
            risk_level = "HIGH (Circular Trading/Revenue Inflation Suspected)"
        elif risk_score > 20:
            risk_level = "MEDIUM"
            
        return {
            "months_analyzed": total_months,
            "anomalous_months_detected": anomaly_count,
            "anomaly_risk_score": risk_score,
            "assessed_risk_level": risk_level
        }

if __name__ == "__main__":
    # Test the Anomaly Pipeline
    detector = FinancialAnomalyDetector()
    
    mock_data = "data/mock/gst_bank_mock_data.csv"
    if not os.path.exists(mock_data):
        print("Mock data missing. Generating now...")
        from src.anomaly_detection.data_generator import generate_mock_financial_data
        generate_mock_financial_data()
        
    detector.train(mock_data)
    
    # Test on a specific company (e.g. COMP_10)
    df = pd.read_csv(mock_data)
    test_company = df[df['Company_ID'] == "COMP_10"]
    result = detector.predict(test_company)
    
    print("\n--- TEST: Detection on COMP_10 ---")
    print(f"Actual Ground Truth Fraud Flag: {test_company['Is_Fraudulent_Flag'].iloc[0]}")
    print(f"Model Assessment: {result}")
