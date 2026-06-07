import numpy as np
import pandas as pd


class InferenceService:
    def __init__(self, model_loader):
        self.model_loader = model_loader

    def predict(self, features_dict):
        model = self.model_loader.get_model()
        if model is None:
            raise RuntimeError("Модель не загружена")

        feature_order = [
            'rate_last_30min', 'total_uphills', 'cv_intervals', 'entropy_turnstiles',
            'top1_turnstile_ratio', 'bigram_prob', 'current_pause_minutes',
            'is_lunch_time', 'hour_of_day', 'ratio_rate_last_to_early',
            'share_olympia', 'ratio_olympia_spike',
            'share_green', 'share_blue', 'share_red', 'share_black',
            'share_south_slope', 'share_north_slope'
        ]
        # Создаём DataFrame с одной строкой и правильными именами колонок
        X_df = pd.DataFrame([features_dict], columns=feature_order)
        prob = model.predict_proba(X_df)[0, 1]
        return prob