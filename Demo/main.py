import time
from modules.config_manager import ConfigManager
from modules.model_loader import ModelLoader
from modules.data_connector import DataConnector
from modules.feature_service import FeatureService
from modules.inference_service import InferenceService
from modules.state_store import StateStore
from modules.ranking_engine import RankingEngine
from modules.audit_logger import AuditLogger
from modules.scheduler import Scheduler
from modules.web_ui import start_web
import threading


def main():
    config = ConfigManager('config.yaml')
    model_loader = ModelLoader(config)
    data_connector = DataConnector(config)
    feature_service = FeatureService(config)
    inference_service = InferenceService(model_loader)
    state_store = StateStore(config)
    ranking_engine = RankingEngine(state_store, config)
    audit_logger = AuditLogger(config)

    # Планировщик
    scheduler = Scheduler(config, feature_service, state_store, model_loader)
    scheduler.start()

    # Запуск веб-интерфейса в отдельном потоке
    web_thread = threading.Thread(target=start_web, args=(
        config.get('web_host'), config.get('web_port'), config.get('web_debug', False),
        ranking_engine, audit_logger, state_store
    ), daemon=True)
    web_thread.start()

    # Основной цикл обработки событий (имитация потока)
    print("Система запущена. Ожидание событий...")
    current_day = None
    while True:
        event = data_connector.get_next_event()
        if event is None:
            print("Все события обработаны.")
            break

        # Определяем дату события
        event_date = event['dt_usages'].date()

        # При смене дня — сбрасываем состояние и кэш
        if current_day is None or event_date != current_day:
            print(f"Новый день: {event_date}. Сброс состояния.")
            state_store.reset_day()
            feature_service.clear_day_cache()
            current_day = event_date

        try:
            ticket = event['ticket_number']
            feature_service.add_event(event)
            features = feature_service.compute_features_for_ticket(ticket)
            if features:
                score = inference_service.predict(features)
                ranking_engine.process_new_slice(ticket, score, event['dt_usages'], features)
        except Exception as e:
            print(f"Ошибка обработки события: {e}")
            import traceback
            traceback.print_exc()

        time.sleep(0.1)

    # После обработки всех событий даём поработать вебу
    print("Обработка завершена. Нажмите Ctrl+C для выхода.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    scheduler.shutdown()
    state_store.save_state()
    print("Система остановлена.")

if __name__ == '__main__':
    main()