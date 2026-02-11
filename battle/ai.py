"""Intelligence artificielle simple pour le combat Pokemon."""

import random


class AIOpponent:
    """IA qui selectionne la meilleure attaque pour un Pokemon."""

    def __init__(self, pokemon, type_chart):
        self.pokemon = pokemon
        self.type_chart = type_chart

    def choose_move(self, opponent):
        """Choisit une attaque contre l'adversaire.

        Strategie :
        - Score chaque move selon puissance * efficacite * STAB
        - 70% de chance de choisir le meilleur move
        - 30% de chance de choisir un move aleatoire
        """
        available_moves = [m for m in self.pokemon.moves if m.has_pp()]

        if not available_moves:
            # Retourne le premier move meme sans PP (struggle)
            return self.pokemon.moves[0]

        # Scorer chaque move
        scored_moves = []
        for move in available_moves:
            score = self._score_move(move, opponent)
            scored_moves.append((move, score))

        # Trier par score decroissant
        scored_moves.sort(key=lambda x: x[1], reverse=True)

        # 70% meilleur move, 30% aleatoire
        if random.random() < 0.7:
            return scored_moves[0][0]
        else:
            return random.choice(available_moves)

    def _score_move(self, move, opponent):
        """Score un move selon son efficacite estimee."""
        if not move.is_damaging():
            # Les moves de statut ont un score fixe bas
            return 20.0

        power = move.power
        effectiveness = self.type_chart.get_effectiveness(move.move_type, opponent.types)

        # Bonus STAB
        stab = 1.5 if move.move_type in self.pokemon.types else 1.0

        return power * effectiveness * stab
