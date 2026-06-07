import pandas as pd
import os
from threading import Lock
from datetime import datetime

class StateStore:
    def __init__(self, config):
        self.config = config
        self.state = {}  # ticket -> {max_score, last_score, last_event_time, blocked, ...}
        self.lock = Lock()
        self.load_state()

    def load_state(self):
        path = self.config.get("state_csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            for _, row in df.iterrows():
                self.state[row['ticket_number']] = {
                    'max_score': row['max_score'],
                    'last_score': row['last_score'],
                    'last_event_time': pd.to_datetime(row['last_event_time']),
                    'blocked': row.get('blocked', False)
                }

    def save_state(self):
        path = self.config.get("state_csv")
        with self.lock:
            records = []
            for ticket, data in self.state.items():
                records.append({
                    'ticket_number': ticket,
                    'max_score': data['max_score'],
                    'last_score': data['last_score'],
                    'last_event_time': data['last_event_time'].strftime('%Y-%m-%d %H:%M:%S'),
                    'blocked': data.get('blocked', False)
                })
            pd.DataFrame(records).to_csv(path, index=False)

    def update_score(self, ticket, score, timestamp):
        with self.lock:
            if ticket not in self.state:
                self.state[ticket] = {'max_score': 0, 'last_score': 0,
                                      'last_event_time': timestamp, 'blocked': False}
            entry = self.state[ticket]
            entry['last_score'] = score
            entry['last_event_time'] = max(entry['last_event_time'], timestamp)
            entry['max_score'] = max(entry['max_score'], score)

    def get_top_n(self, n):
        with self.lock:
            items = sorted(self.state.items(), key=lambda x: x[1]['max_score'], reverse=True)
            return items[:n]

    def block_ticket(self, ticket):
        with self.lock:
            if ticket in self.state:
                self.state[ticket]['blocked'] = True

    def reset_day(self):
        with self.lock:
            self.state.clear()