"""Classe Battle orchestrant un combat Pokemon complet."""

import random

from battle.damage_calculator import DamageCalculator


class Battle:
    """Gere la logique d'un combat entre deux Pokemon."""

    def __init__(self, pokemon1, pokemon2, type_chart):
        self.pokemon1 = pokemon1  # Pokemon du joueur 1
        self.pokemon2 = pokemon2  # Pokemon du joueur 2
        self.type_chart = type_chart
        self.damage_calc = DamageCalculator(type_chart)

        self.turn_number = 0
        self.is_over = False
        self.winner = None
        self.loser = None

    def execute_turn(self, move1, move2):
        """Execute un tour complet. Retourne la liste des messages."""
        self.turn_number += 1
        messages = []

        # Determiner l'ordre d'attaque par la vitesse
        first, first_move, second, second_move = self._determine_order(
            self.pokemon1, move1, self.pokemon2, move2
        )

        # Premier attaquant
        msgs = self._process_turn(first, second, first_move)
        messages.extend(msgs)

        # Verifier si le defenseur est KO
        if second.is_fainted():
            self.is_over = True
            self.winner = first
            self.loser = second
            messages.append(f"{second.name} est K.O. !")
            messages.append(f"{first.name} remporte le combat !")
            return messages

        # Second attaquant
        msgs = self._process_turn(second, first, second_move)
        messages.extend(msgs)

        # Verifier si le premier est KO
        if first.is_fainted():
            self.is_over = True
            self.winner = second
            self.loser = first
            messages.append(f"{first.name} est K.O. !")
            messages.append(f"{second.name} remporte le combat !")
            return messages

        # Degats de fin de tour (poison, brulure)
        for pokemon in [first, second]:
            if pokemon.status and pokemon.status.is_active:
                msg = pokemon.status.on_turn_end(pokemon)
                if msg:
                    messages.append(msg)
                # Retirer le statut s'il n'est plus actif
                if not pokemon.status.is_active:
                    pokemon.status = None

                # Verifier KO apres degats de statut
                if pokemon.is_fainted():
                    other = second if pokemon == first else first
                    self.is_over = True
                    self.winner = other
                    self.loser = pokemon
                    messages.append(f"{pokemon.name} est K.O. !")
                    messages.append(f"{other.name} remporte le combat !")
                    return messages

        return messages

    def _process_turn(self, attacker, defender, move):
        """Traite le tour d'un Pokemon : statut, attaque, degats."""
        messages = []

        # Verifier le statut en debut de tour
        can_move, status_msg = self._process_status_start(attacker)
        if status_msg:
            messages.append(status_msg)
        if not can_move:
            return messages

        # Utiliser le move
        messages.append(f"{attacker.name} utilise {move.display_name} !")
        move.use()

        # Verifier la precision
        if not self._check_accuracy(move):
            messages.append(f"Mais l'attaque de {attacker.name} a echoue !")
            return messages

        # Calculer et appliquer les degats
        effectiveness = 1.0
        if move.is_damaging():
            result = self.damage_calc.calculate(attacker, defender, move)
            effectiveness = result.effectiveness
            defender.take_damage(result.damage)

            if result.effectiveness == 0:
                messages.append("Cela n'a aucun effet...")
            else:
                messages.append(f"{defender.name} perd {result.damage} PV !")

                # Message d'efficacite
                eff_text = self.type_chart.get_effectiveness_text(result.effectiveness)
                if eff_text:
                    messages.append(eff_text)

                # Coup critique
                if result.is_critical:
                    messages.append("Coup critique !")

        # Appliquer l'effet de statut
        if move.ailment and effectiveness > 0:
            ailment_msg = self._apply_ailment(move, defender)
            if ailment_msg:
                messages.append(ailment_msg)

        return messages

    def _process_status_start(self, pokemon):
        """Traite les effets de statut en debut de tour."""
        if pokemon.status and pokemon.status.is_active:
            can_move, msg = pokemon.status.on_turn_start(pokemon)
            if not pokemon.status.is_active:
                pokemon.status = None
            return can_move, msg
        return True, ""

    def _check_accuracy(self, move):
        """Verifie si l'attaque touche."""
        return random.randint(1, 100) <= move.accuracy

    def _apply_ailment(self, move, target):
        """Tente d'appliquer un effet de statut."""
        if move.ailment and move.ailment_chance > 0:
            if random.randint(1, 100) <= move.ailment_chance:
                return target.apply_status(move.ailment)
        elif move.ailment and move.ailment_chance == 0 and not move.is_damaging():
            # Les moves de statut purs appliquent toujours leur effet
            return target.apply_status(move.ailment)
        return ""

    def _determine_order(self, pokemon1, move1, pokemon2, move2):
        """Determine l'ordre d'attaque selon la vitesse."""
        speed1 = pokemon1.get_effective_speed()
        speed2 = pokemon2.get_effective_speed()

        if speed1 > speed2:
            return pokemon1, move1, pokemon2, move2
        elif speed2 > speed1:
            return pokemon2, move2, pokemon1, move1
        else:
            # Egalite : aleatoire
            if random.random() < 0.5:
                return pokemon1, move1, pokemon2, move2
            return pokemon2, move2, pokemon1, move1
