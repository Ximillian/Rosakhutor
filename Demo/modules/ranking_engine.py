class RankingEngine:
    def __init__(self, state_store, config):
        self.state_store = state_store
        self.top_n = config.get('top_n', 20)

    def process_new_slice(self, ticket, score, timestamp, features):
        self.state_store.update_score(ticket, score, timestamp)
        # Можно дополнительно сохранять признаки для объяснения
        # Пока не сохраняем

    def get_top_suspicious(self):
        return self.state_store.get_top_n(self.top_n)