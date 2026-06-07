import pandas as pd
import numpy as np
from datetime import timedelta
from collections import defaultdict

class FeatureService:
    def __init__(self, config):
        self.config = config
        self.cache = defaultdict(list)  # ticket_number -> список подъёмов (pd.DataFrame)
        self.redis = None               # В демо-версии не используется

    def add_event(self, event):
        ticket = event['ticket_number']
        self.cache[ticket].append(event)
        # Храним как DataFrame для удобства
        # В реальности можно хранить как список словарей и конвертировать при вычислении признаков

    def compute_features_for_ticket(self, ticket, event_idx=None):
        events = self.cache[ticket]
        if len(events) < 2:
            return None
        df = pd.DataFrame(events)
        df = df.sort_values('dt_usages').reset_index(drop=True)
        # Расчёт временных признаков
        df['time_from_start_min'] = (df['dt_usages'] - df['dt_usages'].min()).dt.total_seconds() / 60
        df['interval_min'] = df['dt_usages'].diff().dt.total_seconds() / 60
        df['interval_min'] = df['interval_min'].fillna(0)

        # Если event_idx не указан, берём последний
        idx = event_idx if event_idx is not None else len(df)-1
        now = df.iloc[idx]['dt_usages']
        window_start = now - timedelta(minutes=self.config.get('window_minutes', 30))
        window = df[(df['dt_usages'] >= window_start) & (df['dt_usages'] <= now)]
        all_events = df.iloc[:idx+1]

        # Признаки
        rate = len(window) / (self.config.get('window_minutes', 30)/60) if len(window)>0 else 0
        total = len(all_events)

        if len(window) >= 2:
            intervals = window['interval_min'].values[1:]
            cv = np.std(intervals) / (np.mean(intervals)+1e-6) if len(intervals)>=2 else 0
        else:
            cv = 0

        probs = window['turnstile_usages'].value_counts(normalize=True)
        entropy = -np.sum(probs * np.log2(probs+1e-9)) if len(probs)>0 else 0
        top1 = probs.max() if len(probs)>0 else 0

        if len(all_events) >= 2:
            prev, curr = all_events.iloc[-2]['turnstile_usages'], all_events.iloc[-1]['turnstile_usages']
            pairs = [(all_events.iloc[i-1]['turnstile_usages'], all_events.iloc[i]['turnstile_usages']) for i in range(1, len(all_events))]
            pair_counts = pd.Series(pairs).value_counts()
            bigram = (pair_counts.get((prev,curr),0)+1) / (len(pairs)+len(pair_counts)+1e-6)
        else:
            bigram = 0

        pause = (now - df.iloc[idx-1]['dt_usages']).total_seconds()/60 if idx>0 else 0
        lunch = 1 if (self.config.get('lunch_start') <= now.hour < self.config.get('lunch_end')) else 0

        early = all_events[all_events['time_from_start_min'] <= self.config.get('early_profile_minutes', 90)]
        early_rate = len(early) / (self.config.get('early_profile_minutes', 90)/60) if len(early)>0 else 1e-6
        ratio_rate = rate / early_rate if early_rate>0 else 0

        share_olympia = window['turnstile_usages'].str.contains('Олимпия', na=False).mean() if len(window)>0 else 0
        if len(early) > 0:
            early_olympia = early['turnstile_usages'].str.contains('Олимпия', na=False).mean()
        else:
            early_olympia = 0.0
        ratio_olympia = share_olympia / early_olympia if early_olympia != 0 else 0.0

        # Доли one-hot-признаков (предполагаем, что колонки уже есть)
        shares = {}
        for col in ['green', 'blue', 'red', 'black', 'south_slope', 'north_slope']:
            shares[col] = window[col].mean() if col in window.columns else 0

        return {
            'rate_last_30min': rate, 'total_uphills': total, 'cv_intervals': cv,
            'entropy_turnstiles': entropy, 'top1_turnstile_ratio': top1,
            'bigram_prob': bigram, 'current_pause_minutes': pause,
            'is_lunch_time': lunch, 'hour_of_day': now.hour,
            'ratio_rate_last_to_early': ratio_rate,
            'share_olympia': share_olympia, 'ratio_olympia_spike': ratio_olympia,
            **{f'share_{col}': shares[col] for col in ['green','blue','red','black','south_slope','north_slope']}
        }

    def clear_day_cache(self):
        self.cache.clear()