"""Intelligence artificielle pour le combat Pokemon - 3 niveaux de difficulte."""

import random


# Constante pour signaler un switch volontaire
AI_SWITCH = "AI_SWITCH"


class AIOpponent:
    """IA qui selectionne des actions en combat selon le niveau de difficulte.

    Niveaux :
    - "facile"    : choix souvent aleatoire, pas de switch strategique
    - "normal"    : favorise le meilleur move, switch apres KO par matchup de type
    - "difficile" : toujours le meilleur move, switch volontaire strategique
    """

    def __init__(self, pokemon, type_chart, difficulty="normal", team=None):
        self.pokemon = pokemon
        self.type_chart = type_chart
        self.difficulty = difficulty
        self.team = team  # equipe complete pour le switch strategique

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def choose_action(self, opponent, switchable_pokemon=None):
        """Choisit une action : un Move ou AI_SWITCH (+ le pokemon cible).

        Retourne :
            (move, None)          -> l'IA attaque avec ce move
            (AI_SWITCH, pokemon)  -> l'IA veut switcher vers ce pokemon
        """
        if self.difficulty == "difficile" and switchable_pokemon:
            switch_target = self._should_switch(opponent, switchable_pokemon)
            if switch_target:
                return AI_SWITCH, switch_target

        move = self.choose_move(opponent)
        return move, None

    def choose_move(self, opponent):
        """Choisit une attaque contre l'adversaire selon la difficulte."""
        available_moves = [m for m in self.pokemon.moves if m.has_pp()]

        if not available_moves:
            return self.pokemon.moves[0]

        scored_moves = []
        for move in available_moves:
            score = self._score_move(move, opponent)
            scored_moves.append((move, score))

        scored_moves.sort(key=lambda x: x[1], reverse=True)

        if self.difficulty == "facile":
            # 40% meilleur move, 60% aleatoire
            if random.random() < 0.4:
                return scored_moves[0][0]
            else:
                return random.choice(available_moves)

        elif self.difficulty == "normal":
            # 70% meilleur move, 30% aleatoire
            if random.random() < 0.7:
                return scored_moves[0][0]
            else:
                return random.choice(available_moves)

        else:  # difficile
            # Toujours le meilleur move
            return scored_moves[0][0]

    def choose_switch_after_ko(self, alive_pokemon, opponent):
        """Choisit le Pokemon a envoyer apres un KO selon la difficulte."""
        if not alive_pokemon:
            return None

        if self.difficulty == "facile":
            return random.choice(alive_pokemon)

        # Normal et Difficile : choisir le meilleur matchup de type
        return self._best_matchup(alive_pokemon, opponent)

    # ------------------------------------------------------------------
    # Scoring des moves
    # ------------------------------------------------------------------

    def _score_move(self, move, opponent):
        """Score un move selon son efficacite estimee."""
        if not move.is_damaging():
            return self._score_status_move(move, opponent)

        power = move.power
        effectiveness = self.type_chart.get_effectiveness(move.move_type, opponent.types)

        # Bonus STAB
        stab = 1.5 if move.move_type in self.pokemon.types else 1.0

        base_score = power * effectiveness * stab

        if self.difficulty == "difficile":
            # Bonus si le move peut KO l'adversaire
            if effectiveness >= 2.0:
                base_score *= 1.2
            # Malus si immunite
            if effectiveness == 0:
                base_score = 0

        return base_score

    def _score_status_move(self, move, opponent):
        """Score un move de statut selon le contexte."""
        if self.difficulty == "difficile":
            # Les moves de statut sont plus valorises en difficile
            if opponent.status is not None:
                return 5.0  # L'adversaire a deja un statut, peu utile
            if move.ailment == "paralysis":
                # Tres utile si l'adversaire est plus rapide
                if opponent.speed > self.pokemon.speed:
                    return 60.0
                return 35.0
            if move.ailment == "burn":
                # Utile contre les attaquants physiques
                if opponent.attack > opponent.sp_attack:
                    return 55.0
                return 30.0
            if move.ailment in ("sleep", "freeze"):
                return 65.0  # Tres puissant
            if move.ailment == "poison":
                return 40.0
            return 25.0
        else:
            # Facile et Normal : score fixe bas pour les moves de statut
            return 20.0

    # ------------------------------------------------------------------
    # Switch strategique (difficile uniquement)
    # ------------------------------------------------------------------

    def _should_switch(self, opponent, switchable_pokemon):
        """Evalue si l'IA devrait switcher volontairement (mode difficile).

        Criteres :
        - Le Pokemon actuel est desavantage en type
        - Un autre Pokemon a un avantage de type
        - Le Pokemon actuel a encore assez de HP (> 25%) pour que le switch vaille le coup
        """
        if not switchable_pokemon:
            return None

        # Ne pas switcher si le Pokemon est presque KO (le switch serait gache)
        if self.pokemon.hp_percentage() < 0.25:
            return None

        # Evaluer le matchup actuel
        current_score = self._matchup_score(self.pokemon, opponent)

        # Si le matchup actuel est deja bon, pas besoin de switcher
        if current_score >= 1.0:
            return None

        # Chercher un meilleur Pokemon
        best_candidate = None
        best_score = current_score

        for poke in switchable_pokemon:
            score = self._matchup_score(poke, opponent)
            if score > best_score:
                best_score = score
                best_candidate = poke

        # Switcher seulement si le gain est significatif
        if best_candidate and best_score >= 1.5 and best_score > current_score + 0.5:
            # 70% de chance de switcher (pour ne pas etre trop previsible)
            if random.random() < 0.7:
                return best_candidate

        return None

    # ------------------------------------------------------------------
    # Matchup de type
    # ------------------------------------------------------------------

    def _matchup_score(self, pokemon, opponent):
        """Calcule un score de matchup de type entre un Pokemon et l'adversaire.

        Prend en compte :
        - Les degats que le Pokemon peut infliger (types offensifs)
        - Les degats que le Pokemon subirait (types defensifs)
        """
        offensive_score = 0.0
        for poke_type in pokemon.types:
            eff = self.type_chart.get_effectiveness(poke_type, opponent.types)
            offensive_score = max(offensive_score, eff)

        defensive_score = 0.0
        for opp_type in opponent.types:
            eff = self.type_chart.get_effectiveness(opp_type, pokemon.types)
            defensive_score = max(defensive_score, eff)

        # Score final : bon offensivement et resistant defensivement
        if defensive_score == 0:
            defense_factor = 2.0  # Immunite = excellent
        else:
            defense_factor = 1.0 / defensive_score

        return offensive_score * defense_factor

    def _best_matchup(self, alive_pokemon, opponent):
        """Choisit le Pokemon avec le meilleur matchup de type."""
        best = None
        best_score = -1

        for poke in alive_pokemon:
            score = self._matchup_score(poke, opponent)
            # Bonus leger pour les Pokemon avec plus de HP
            hp_bonus = poke.hp_percentage() * 0.3
            total = score + hp_bonus

            if total > best_score:
                best_score = total
                best = poke

        return best if best else alive_pokemon[0]
