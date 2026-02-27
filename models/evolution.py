"""Systeme d'evolution des Pokemon."""

import json
import os

from config import BASE_DIR


class EvolutionManager:
    """Gere les evolutions des Pokemon en se basant sur bdd/evolutions.json."""

    def __init__(self):
        self.evolution_table = {}
        self._load_evolutions()

    def _load_evolutions(self):
        """Charge la table d'evolutions depuis le fichier JSON."""
        evo_path = os.path.join(BASE_DIR, "bdd", "evolutions.json")
        if os.path.exists(evo_path):
            with open(evo_path, "r", encoding="utf-8") as f:
                self.evolution_table = json.load(f)
            print(f"[Evolution] {len(self.evolution_table)} evolutions chargees")
        else:
            print("[Evolution] ATTENTION: bdd/evolutions.json introuvable")

    def can_evolve(self, pokemon):
        """Verifie si un Pokemon peut evoluer a son niveau actuel."""
        key = str(pokemon.pokemon_id)
        if key not in self.evolution_table:
            return False
        return pokemon.level >= self.evolution_table[key]["level"]

    def get_evolution_id(self, pokemon):
        """Retourne l'ID du Pokemon evolue, ou None."""
        key = str(pokemon.pokemon_id)
        if key not in self.evolution_table:
            return None
        evo_data = self.evolution_table[key]
        if pokemon.level >= evo_data["level"]:
            return evo_data["evolves_to"]
        return None

    def get_evolution_level(self, pokemon_id):
        """Retourne le niveau necessaire pour evoluer, ou None."""
        key = str(pokemon_id)
        if key in self.evolution_table:
            return self.evolution_table[key]["level"]
        return None