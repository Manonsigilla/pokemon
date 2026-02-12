"""Table d'efficacite des types Pokemon - Lit bdd/types.json de Manon."""

import json
import os

from config import BASE_DIR


class TypeChart:
    """Gere les multiplicateurs d'efficacite entre types depuis bdd/types.json."""

    def __init__(self):
        self.chart = {}
        self._load_chart()

    def _load_chart(self):
        """Charge la table de types depuis bdd/types.json (donnees de Manon)."""
        types_path = os.path.join(BASE_DIR, "bdd", "types.json")

        if os.path.exists(types_path):
            with open(types_path, "r", encoding="utf-8") as f:
                type_data = json.load(f)

            # Convertir le format de bdd/types.json vers le format {attaquant: {defenseur: multiplicateur}}
            for atk_type, relations in type_data.items():
                self.chart[atk_type] = {}
                for def_type in relations.get("double_damage_to", []):
                    self.chart[atk_type][def_type] = 2.0
                for def_type in relations.get("half_damage_to", []):
                    self.chart[atk_type][def_type] = 0.5
                for def_type in relations.get("no_damage_to", []):
                    self.chart[atk_type][def_type] = 0.0

            print(f"TypeChart: {len(self.chart)} types charges depuis bdd/types.json")
        else:
            print("ATTENTION: bdd/types.json introuvable, utilisation table par defaut")
            self._load_fallback_chart()

    def _load_fallback_chart(self):
        """Table de secours hardcodee si le fichier JSON est absent."""
        self.chart = {
            "normal": {"rock": 0.5, "ghost": 0.0, "steel": 0.5},
            "fire": {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 2.0,
                     "bug": 2.0, "rock": 0.5, "dragon": 0.5, "steel": 2.0},
            "water": {"fire": 2.0, "water": 0.5, "grass": 0.5, "ground": 2.0,
                      "rock": 2.0, "dragon": 0.5},
            "grass": {"fire": 0.5, "water": 2.0, "grass": 0.5, "poison": 0.5,
                      "ground": 2.0, "flying": 0.5, "bug": 0.5, "rock": 2.0,
                      "dragon": 0.5, "steel": 0.5},
            "electric": {"water": 2.0, "grass": 0.5, "electric": 0.5,
                         "ground": 0.0, "flying": 2.0, "dragon": 0.5},
            "ice": {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 0.5,
                    "ground": 2.0, "flying": 2.0, "dragon": 2.0, "steel": 0.5},
            "fighting": {"normal": 2.0, "ice": 2.0, "poison": 0.5, "flying": 0.5,
                         "psychic": 0.5, "bug": 0.5, "rock": 2.0, "ghost": 0.0,
                         "dark": 2.0, "steel": 2.0, "fairy": 0.5},
            "poison": {"grass": 2.0, "poison": 0.5, "ground": 0.5, "rock": 0.5,
                       "ghost": 0.5, "steel": 0.0, "fairy": 2.0},
            "ground": {"fire": 2.0, "grass": 0.5, "electric": 2.0, "poison": 2.0,
                       "flying": 0.0, "bug": 0.5, "rock": 2.0, "steel": 2.0},
            "flying": {"grass": 2.0, "electric": 0.5, "fighting": 2.0, "bug": 2.0,
                       "rock": 0.5, "steel": 0.5},
            "psychic": {"fighting": 2.0, "poison": 2.0, "psychic": 0.5,
                        "dark": 0.0, "steel": 0.5},
            "bug": {"fire": 0.5, "grass": 2.0, "fighting": 0.5, "poison": 0.5,
                    "flying": 0.5, "psychic": 2.0, "ghost": 0.5, "dark": 2.0,
                    "steel": 0.5, "fairy": 0.5},
            "rock": {"fire": 2.0, "ice": 2.0, "fighting": 0.5, "ground": 0.5,
                     "flying": 2.0, "bug": 2.0, "steel": 0.5},
            "ghost": {"normal": 0.0, "psychic": 2.0, "ghost": 2.0, "dark": 0.5},
            "dragon": {"dragon": 2.0, "steel": 0.5, "fairy": 0.0},
            "dark": {"fighting": 0.5, "psychic": 2.0, "ghost": 2.0, "dark": 0.5,
                     "fairy": 0.5},
            "steel": {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2.0,
                      "rock": 2.0, "steel": 0.5, "fairy": 2.0},
            "fairy": {"fire": 0.5, "fighting": 2.0, "poison": 0.5, "dragon": 2.0,
                      "dark": 2.0, "steel": 0.5},
        }

    def get_effectiveness(self, move_type, defender_types):
        """Calcule le multiplicateur total d'un type d'attaque contre les types du defenseur."""
        multiplier = 1.0
        attack_chart = self.chart.get(move_type, {})
        for def_type in defender_types:
            multiplier *= attack_chart.get(def_type, 1.0)
        return multiplier

    def get_effectiveness_text(self, multiplier):
        """Retourne un texte decrivant l'efficacite."""
        if multiplier == 0:
            return "Cela n'a aucun effet..."
        elif multiplier >= 2.0:
            return "C'est super efficace !"
        elif multiplier < 1.0:
            return "Ce n'est pas tres efficace..."
        return ""