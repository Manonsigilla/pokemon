"""Cache disque pour les reponses API et les sprites."""

import json
import os


class Cache:
    """Cache les donnees API en JSON et les sprites en PNG sur le disque."""

    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Cree les sous-dossiers de cache si necessaire."""
        for sub in ("pokemon", "moves", "types", "sprites"):
            os.makedirs(os.path.join(self.cache_dir, sub), exist_ok=True)

    def get_json(self, category, key):
        """Retourne les donnees JSON cachees ou None si absentes."""
        path = os.path.join(self.cache_dir, category, f"{key}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def save_json(self, category, key, data):
        """Sauvegarde des donnees JSON dans le cache."""
        path = os.path.join(self.cache_dir, category, f"{key}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def get_sprite_path(self, pokemon_id, side="front"):
        """Retourne le chemin du sprite cache ou None si absent."""
        filename = f"{pokemon_id}_{side}.png"
        path = os.path.join(self.cache_dir, "sprites", filename)
        if os.path.exists(path):
            return path
        return None

    def save_sprite(self, pokemon_id, side, image_bytes):
        """Sauvegarde un sprite PNG et retourne son chemin."""
        filename = f"{pokemon_id}_{side}.png"
        path = os.path.join(self.cache_dir, "sprites", filename)
        with open(path, "wb") as f:
            f.write(image_bytes)
        return path
