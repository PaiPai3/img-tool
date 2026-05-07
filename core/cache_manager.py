import os
import json


class CacheManager:
    CACHE_DIR = "cache"
    PIPELINES_DIR = os.path.join(CACHE_DIR, "pipelines")
    SETTINGS_FILE = os.path.join(CACHE_DIR, "settings.json")

    @classmethod
    def ensure_dirs(cls):
        os.makedirs(cls.PIPELINES_DIR, exist_ok=True)

    # --- Settings ---

    @classmethod
    def load_settings(cls) -> dict:
        if not os.path.isfile(cls.SETTINGS_FILE):
            return {}
        try:
            with open(cls.SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    @classmethod
    def save_settings(cls, data: dict):
        os.makedirs(cls.CACHE_DIR, exist_ok=True)
        with open(cls.SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # --- Pipelines ---

    @classmethod
    def save_pipeline(cls, name: str, config: list[dict]):
        os.makedirs(cls.PIPELINES_DIR, exist_ok=True)
        filepath = os.path.join(cls.PIPELINES_DIR, f"{name}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_pipeline(cls, name: str) -> list[dict] | None:
        filepath = os.path.join(cls.PIPELINES_DIR, f"{name}.json")
        if not os.path.isfile(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    @classmethod
    def list_pipelines(cls) -> list[str]:
        if not os.path.isdir(cls.PIPELINES_DIR):
            return []
        return sorted(
            f.replace(".json", "")
            for f in os.listdir(cls.PIPELINES_DIR)
            if f.endswith(".json")
        )

    @classmethod
    def delete_pipeline(cls, name: str):
        filepath = os.path.join(cls.PIPELINES_DIR, f"{name}.json")
        if os.path.isfile(filepath):
            os.remove(filepath)
