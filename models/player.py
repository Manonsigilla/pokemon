"""Classe representant un dresseur Pokemon."""

class Player:
    """Dresseur avec une equipe de Pokemon."""

    MAX_TEAM_SIZE = 6

    def __init__(self, name, is_ai=False):
        self.name = name
        self.team = []  # Liste de Pokemon (max 6)
        self.is_ai = is_ai

        # Pokedex simplifie (listes d'IDs) - la vraie classe viendra plus tard
        self.pokedex_seen = []
        self.pokedex_caught = []

    def add_pokemon(self, pokemon):
        """Ajoute un Pokemon a l'equipe (max 6). Retourne True si ok."""
        if len(self.team) < self.MAX_TEAM_SIZE:
            self.team.append(pokemon)

            # Enregistrer dans le pokedex
            if pokemon.pokemon_id not in self.pokedex_caught:
                self.pokedex_caught.append(pokemon.pokemon_id)
            if pokemon.pokemon_id not in self.pokedex_seen:
                self.pokedex_seen.append(pokemon.pokemon_id)

            return True
        return False

    def get_active_pokemon(self):
        """Retourne le premier Pokemon non KO de l'equipe."""
        for poke in self.team:
            if not poke.is_fainted():
                return poke
        return None

    def has_alive_pokemon(self):
        """Verifie si au moins un Pokemon est encore en vie."""
        return any(not p.is_fainted() for p in self.team)

    def get_alive_pokemon(self):
        """Retourne la liste des Pokemon non KO."""
        return [p for p in self.team if not p.is_fainted()]

    def get_switchable_pokemon(self, current_pokemon):
        """Retourne les Pokemon vivants sauf celui actif."""
        return [p for p in self.team if not p.is_fainted() and p != current_pokemon]

    def heal_all(self):
        """Soigne toute l'equipe (Centre Pokemon)."""
        for pokemon in self.team:
            pokemon.current_hp = pokemon.max_hp
            pokemon.status = None
            for move in pokemon.moves:
                move.current_pp = move.max_pp

    def __str__(self):
        alive = len(self.get_alive_pokemon())
        return f"{self.name} ({alive}/{len(self.team)} Pokemon)"
    def save_team_to_pokedex(self, combat):
        """Enregistre tous les Pokemon de l'equipe dans le Pokedex.
        
        Args:
            combat (Combat): Instance de la classe Combat
        """
        for pokemon in self.team:
            combat.save_to_pokedex(pokemon)