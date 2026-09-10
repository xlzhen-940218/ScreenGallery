import json
import os

class Config:
    def __init__(self, config_path="data/config.json"):
        self.config_path = config_path
        self._data = {
            "photo_dir": ""
        }
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._data.update(data)
            except Exception as e:
                print(f"Failed to load config: {e}")

    def save(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def get_photo_dir(self):
        return self._data.get("photo_dir", "")

    def set_photo_dir(self, path):
        self._data["photo_dir"] = path
        self.save()
