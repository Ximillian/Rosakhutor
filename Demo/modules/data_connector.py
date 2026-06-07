import pandas as pd
from datetime import datetime, timedelta


class DataConnector:
    def __init__(self, config):
        # Загрузка основного датасета
        self.df = pd.read_csv(config.get("data_csv"), sep=';',
                              parse_dates=['dt_usages', 'ticket_start_date',
                                           'ticket_end_date', 'blocked_dt'])

        # Загрузка справочника характеристик канатных дорог
        lift_attrs = pd.read_csv('KD-trass.csv', sep=';')
        lift_attrs.columns = lift_attrs.columns.str.strip().str.lower().str.replace(' ', '_')

        # Присоединение к основному датафрейму
        self.df = self.df.merge(lift_attrs, on='turnstile_usages', how='left')
        for col in ['green', 'blue', 'red', 'black', 'south_slope', 'north_slope']:
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna(0).astype(int)
            else:
                self.df[col] = 0  # на случай отсутствия

        # Фильтрация и предобработка
        self.df = self.df[self.df['ticket_ski_days'] == 1].copy()
        self.df = self.df[~self.df['turnstile_usages'].str.contains('спуск', case=False, na=False)]
        self.df = self.df.sort_values(['ticket_number', 'dt_usages']).reset_index(drop=True)

        self.events = self.df.to_dict('records')
        self.current_index = 0

    def get_next_event(self):
        if self.current_index < len(self.events):
            event = self.events[self.current_index]
            self.current_index += 1
            return event
        return None

    def reset(self):
        self.current_index = 0