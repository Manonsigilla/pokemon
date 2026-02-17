"""Classe Combat - Gestion du systeme de combat Pokemon"""

import json
import os
from config import BASE_DIR


class Combat:
    """Classe pour gerer les combats Pokemon et le Pokedex.
    
    Cette classe encapsule la logique de combat et de gestion du Pokedex.
    """
    
    def __init__(self, type_chart):
        """Initialise le systeme de combat.
        
        Args:
            type_chart (TypeChart): Instance du tableau des types
        """
        self.type_chart = type_chart
        self.pokedex_file = os.path.join(BASE_DIR, "pokedex.json")
    
    
    
    def get_type_effectiveness_and_multiply_attack(self, attack_type, defense_types, base_attack):
        """Recupere l'efficacite du type et multiplie la puissance d'attaque.
        
        Selon le tableau des types :
        - Eau vs Feu = 2.0 (super efficace)
        - Feu vs Terre = 0.5 (peu efficace)
        - Normal vs Spectre = 0.0 (aucun effet)
        
        Args:
            attack_type (str): Type de l'attaque (ex: "water", "fire")
            defense_types (list): Liste des types du defenseur (ex: ["grass", "poison"])
            base_attack (int/float): Puissance d'attaque de base
            
        Returns:
            tuple: (degats_multiplies, multiplicateur_efficacite)
            
        Exemple:
            >>> combat = Combat(type_chart)
            >>> degats, efficacite = combat.get_type_effectiveness_and_multiply_attack(
            ...     "water", ["fire"], 10
            ... )
            >>> print(degats)  # 20 (car 10 * 2.0)
            >>> print(efficacite)  # 2.0
        """
        # Recuperer l'efficacite depuis le TypeChart
        effectiveness = self.type_chart.get_effectiveness(attack_type, defense_types)
        
        # Multiplier la puissance d'attaque
        modified_attack = base_attack * effectiveness
        
        return modified_attack, effectiveness
    
    def remove_hp(self, pokemon, damage, defense):
        """Enleve des points de vie en fonction de la defense.
        
        La defense reduit les degats subis. 
        Formule simplifiee : degats_finaux = max(1, damage - defense/2)
        
        Args:
            pokemon (Pokemon): Le Pokemon qui subit les degats
            damage (int): Degats bruts de l'attaque
            defense (int): Stat de defense du Pokemon
            
        Returns:
            int: Points de vie retires
            
        Exemple:
            >>> combat.remove_hp(pikachu, 50, 40)  # degats = 50 - 40/2 = 30
        """
        # La defense reduit les degats (formule simplifiee)
        # Dans le vrai jeu, c'est plus complexe mais on respecte la consigne
        damage_reduction = defense // 2
        final_damage = max(1, damage - damage_reduction)  # Minimum 1 PV de degats
        
        # Appliquer les degats au Pokemon
        pokemon.take_damage(final_damage)
        
        return final_damage
    
    def get_winner_name(self, pokemon1, pokemon2):
        """Renvoie le nom du vainqueur (celui qui n'est pas KO).
        
        Args:
            pokemon1 (Pokemon): Premier Pokemon
            pokemon2 (Pokemon): Deuxieme Pokemon
            
        Returns:
            str: Nom du Pokemon gagnant, ou None si aucun n'est KO
            
        Exemple:
            >>> winner = combat.get_winner_name(pikachu, raichu)
            >>> print(winner)  # "Pikachu" si Raichu est KO
        """
        if pokemon1.is_fainted() and not pokemon2.is_fainted():
            return pokemon2.name
        elif pokemon2.is_fainted() and not pokemon1.is_fainted():
            return pokemon1.name
        else:
            return None  # Aucun gagnant clair (les deux KO ou les deux vivants)
    
    def get_loser_name(self, pokemon1, pokemon2):
        """Renvoie le nom du Pokemon perdant (celui qui est KO).
        
        Args:
            pokemon1 (Pokemon): Premier Pokemon
            pokemon2 (Pokemon): Deuxieme Pokemon
            
        Returns:
            str: Nom du Pokemon perdant, ou None si aucun n'est KO
        """
        if pokemon1.is_fainted():
            return pokemon1.name
        elif pokemon2.is_fainted():
            return pokemon2.name
        else:
            return None
    
    def save_to_pokedex(self, pokemon):
        """Enregistre le Pokemon rencontre dans le fichier pokedex.json.
        
        Verifie les doublons avant d'enregistrer.
        
        Args:
            pokemon (Pokemon): Le Pokemon a enregistrer
            
        Returns:
            bool: True si enregistre, False si doublon
            
        Structure du pokedex.json :
        {
            "pokemon": [
                {
                    "id": 25,
                    "name": "pikachu",
                    "type": ["electric"],
                    "defense": 40,
                    "attack": 55,
                    "hp": 35
                }
            ],
            "count": 1
        }
        """
        # Charger le pokedex existant
        pokedex_data = self._load_pokedex()
        
        # Verifier si le Pokemon existe deja (eviter les doublons)
        for entry in pokedex_data.get("pokemon", []):
            if entry["id"] == pokemon.pokemon_id:
                return False  # Doublon detecte
        
        # Creer l'entree du Pokemon
        pokemon_entry = {
            "id": pokemon.pokemon_id,
            "name": pokemon.name.lower(),
            "type": pokemon.types,
            "defense": pokemon.defense,
            "attack": pokemon.attack,
            "hp": pokemon.max_hp
        }
        
        # Ajouter au pokedex
        if "pokemon" not in pokedex_data:
            pokedex_data["pokemon"] = []
        
        pokedex_data["pokemon"].append(pokemon_entry)
        pokedex_data["count"] = len(pokedex_data["pokemon"])
        
        # Sauvegarder
        self._save_pokedex(pokedex_data)
        
        return True
    
    # =========================================================================
    # Méthodes utilitaires pour le Pokédex
    # =========================================================================
    
    def _load_pokedex(self):
        """Charge le fichier pokedex.json ou cree une structure vide."""
        if os.path.exists(self.pokedex_file):
            with open(self.pokedex_file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {"pokemon": [], "count": 0}
    
    def _save_pokedex(self, data):
        """Sauvegarde le pokedex dans le fichier JSON."""
        with open(self.pokedex_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    def get_pokedex_count(self):
        """Retourne le nombre de Pokemon dans le Pokedex."""
        data = self._load_pokedex()
        return data.get("count", 0)
    
    def get_all_pokemon(self):
        """Retourne la liste de tous les Pokemon dans le Pokedex."""
        data = self._load_pokedex()
        return data.get("pokemon", [])
    
    def display_pokedex(self):
        """Affiche le contenu du Pokedex (pour debug/console)."""
        data = self._load_pokedex()
        print(f"\n=== POKEDEX ({data.get('count', 0)} Pokemon) ===")
        for poke in data.get("pokemon", []):
            print(f"#{poke['id']} - {poke['name'].title()} ({', '.join(poke['type'])})")
            print(f"   HP: {poke['hp']} | Attaque: {poke['attack']} | Defense: {poke['defense']}")