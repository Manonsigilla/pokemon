"""Gestionnaire de sauvegarde de partie (fichier savegame.json)."""

import json
import os
from config import BASE_DIR


SAVE_FILE = os.path.join(BASE_DIR, "savegame.json")


def save_exists():
    """Verifie si une sauvegarde existe."""
    return os.path.exists(SAVE_FILE)


def save_game(starter_id, starter_name, player_pos=None):
    """Sauvegarde la partie en cours.

    Args:
        starter_id (int): ID du Pokemon starter choisi
        starter_name (str): Nom du starter
        player_pos (list): Position [x, y] du joueur sur la carte
    """
    data = {
        "starter_id": starter_id,
        "starter_name": starter_name,
        "player_pos": player_pos or [1, 1]
    }
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_game():
    """Charge la sauvegarde. Retourne le dict ou None si inexistante."""
    if not save_exists():
        return None
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_save():
    """Supprime la sauvegarde si elle existe."""
    if save_exists():
        os.remove(SAVE_FILE)
