import joblib
import os
import time
from threading import Lock

class ModelLoader:
    def __init__(self, config):
        self.config = config
        self.model = None
        self.metadata = {}
        self.lock = Lock()
        self.load_model()

    def load_model(self):
        path = self.config.get("model_path")
        if os.path.exists(path):
            with self.lock:
                self.model = joblib.load(path)
                self.metadata['loaded_at'] = time.time()
                # Можно извлечь AUC из названия или отдельного файла метаданных
                self.metadata['version'] = os.path.basename(path)
        else:
            raise FileNotFoundError(f"Модель не найдена: {path}")

    def reload_if_updated(self):
        # Упрощённо: проверяем время модификации файла
        path = self.config.get("model_path")
        if os.path.exists(path):
            mtime = os.path.getmtime(path)
            if mtime > self.metadata.get('file_mtime', 0):
                self.load_model()
                self.metadata['file_mtime'] = mtime
                return True
        return False

    def get_model(self):
        with self.lock:
            return self.model