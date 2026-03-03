import pandas as pd
import numpy as np
import joblib
import os
import logging

logger = logging.getLogger(__name__)

class FinancialAnomalyDetector:
    def __init__(self, model_path=None):
        if model_path is None:
            # Resolve path relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base_dir, "models", "isolation_forest.pkl")
        self.model_path = model_path
        self._model = None
        self.features = ['GSTR_Mismatch_Ratio', 'Bank_vs_GST_Ratio', 'Velocity_Ratio']

    @property
    def model(self):
        if self._model is None:
            if os.path.exists(self.model_path):
                self._model = joblib.load(self.model_path)
            else:
                logger.warning(f"Anomaly model not found at {self.model_path}. Using fallback logic.")
        return self._model

    def predict(self, gstr_3b: float, gstr_2a: float, bank_in: float, bank_out: float) -> dict:
        """
        Runs the Isolation Forest logic on a single month's data.
        In a real app, this would take a timeseries, but for the hackathon demo,
        we can simulate a 12-month series based on this one data point to show the model in action.
        """
        # Calculate features
        mismatch = abs(gstr_3b - gstr_2a) / (gstr_3b + 1)
        bank_gst_ratio = bank_in / (gstr_3b + 1)
        velocity = bank_in / (bank_out + 1)

        # Construct a small dataframe for prediction
        # To make the 'IsolationForest' work, we'll simulate 12 months where 1 month is this one
        # and the others are slightly jittered versions of it.
        data = []
        for _ in range(12):
            data.append({
                'GSTR_Mismatch_Ratio': mismatch * (1 + np.random.normal(0, 0.05)),
                'Bank_vs_GST_Ratio': bank_gst_ratio * (1 + np.random.normal(0, 0.05)),
                'Velocity_Ratio': velocity * (1 + np.random.normal(0, 0.05))
            })
        
        df = pd.DataFrame(data)
        
        if self.model:
            predictions = self.model.predict(df[self.features])
            anomaly_count = int(sum(predictions == -1))
        else:
            # Fallback heuristic if model pkl is missing
            anomaly_score = 0
            if mismatch > 0.4: anomaly_score += 4
            if bank_gst_ratio > 3.0: anomaly_score += 4
            if 0.9 < velocity < 1.1 and bank_in > 1000000: anomaly_score += 4
            anomaly_count = min(12, anomaly_score)

        risk_score = round((anomaly_count / 12) * 100, 1)
        
        risk_level = "LOW"
        if risk_score > 50:
            risk_level = "HIGH (Suspicious Loops Detected)"
        elif risk_score > 20:
            risk_level = "MEDIUM"
            
        return {
            "anomaly_risk_score": risk_score,
            "anomalous_months": anomaly_count,
            "risk_level": risk_level,
            "metrics": {
                "mismatch_ratio": round(mismatch, 3),
                "bank_to_gst_ratio": round(bank_gst_ratio, 3),
                "money_velocity": round(velocity, 3)
            }
        }

# Singleton instance
detector = FinancialAnomalyDetector()
