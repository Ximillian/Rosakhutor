from apscheduler.schedulers.background import BackgroundScheduler

class Scheduler:
    def __init__(self, config, feature_service, state_store, model_loader):
        self.config = config
        self.feature_service = feature_service
        self.state_store = state_store
        self.model_loader = model_loader
        self.scheduler = BackgroundScheduler()

    def start(self):
        # Очистка кеша каждый день в 23:59
        self.scheduler.add_job(self.midnight_cleanup, 'cron', hour=23, minute=59)
        # Перезагрузка модели каждые 10 минут (проверка обновления)
        self.scheduler.add_job(self.check_model_update, 'interval', minutes=10)
        # Сохранение состояния каждую минуту
        self.scheduler.add_job(self.state_store.save_state, 'interval', minutes=1)
        self.scheduler.start()

    def midnight_cleanup(self):
        self.feature_service.clear_day_cache()
        # Сброс max_score? Не обязательно, но можно перенести в архив
        self.state_store.state.clear()

    def check_model_update(self):
        if self.model_loader.reload_if_updated():
            print("Модель обновлена")

    def shutdown(self):
        self.scheduler.shutdown()