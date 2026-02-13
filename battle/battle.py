"""Classe Battle orchestrant un combat Pokemon complet (equipe vs equipe)."""

import random

from battle.damage_calculator import DamageCalculator


class Battle:
    """Gere la logique d'un combat entre deux equipes de Pokemon.

    Supporte le mode arene (equipe vs equipe) et le mode sauvage (1 pokemon).
    """

    def __init__(self, player1, player2, type_chart, battle_type="arena"):
        """
        Args:
            player1: Player du joueur 1
            player2: Player du joueur 2 (ou IA)
            type_chart: TypeChart pour les calculs d'efficacite
            battle_type: "arena" pour arene, "wild" pour pokemon sauvage (futur)
        """
        self.player1 = player1
        self.player2 = player2
        self.type_chart = type_chart
        self.damage_calc = DamageCalculator(type_chart)
        self.battle_type = battle_type

        # Pokemon actifs sur le terrain
        self.pokemon1 = player1.get_active_pokemon()
        self.pokemon2 = player2.get_active_pokemon()

        self.turn_number = 0
        self.is_over = False
        self.winner = None  # Le Player gagnant
        self.loser = None   # Le Player perdant

        # Gestion des switchs en cours de tour
        self._p1_switched = False
        self._p2_switched = False

    def switch_pokemon(self, player_num, new_pokemon):
        """Change le Pokemon actif d'un joueur. Retourne les messages."""
        messages = []

        if player_num == 1:
            old_name = self.pokemon1.name
            self.pokemon1 = new_pokemon
            self._p1_switched = True
            messages.append(f"{old_name}, reviens !")
            messages.append(f"A toi, {new_pokemon.name} !")
        else:
            old_name = self.pokemon2.name
            self.pokemon2 = new_pokemon
            self._p2_switched = True
            messages.append(f"{old_name}, reviens !")
            messages.append(f"A toi, {new_pokemon.name} !")

        return messages

    def execute_turn(self, move1, move2):
        """Execute un tour complet. Retourne la liste des messages."""
        self.turn_number += 1
        messages = []

        # Reset switch flags
        self._p1_switched = False
        self._p2_switched = False

        # Determiner l'ordre d'attaque par la vitesse
        first, first_move, second, second_move = self._determine_order(
            self.pokemon1, move1, self.pokemon2, move2
        )

        # Premier attaquant
        msgs = self._process_turn(first, second, first_move)
        messages.extend(msgs)

        # Verifier si le defenseur est KO
        if second.is_fainted():
            messages.append(f"{second.name} est K.O. !")

            # Verifier si le dresseur adverse a encore des Pokemon
            loser_player = self.player2 if second == self.pokemon2 else self.player1
            winner_player = self.player1 if loser_player == self.player2 else self.player2

            if not loser_player.has_alive_pokemon():
                self.is_over = True
                self.winner = winner_player
                self.loser = loser_player
                messages.append(f"{winner_player.name} remporte le combat !")
            else:
                # Le perdant doit choisir un nouveau Pokemon
                messages.append(f"{loser_player.name} doit envoyer un autre Pokemon !")
            return messages

        # Second attaquant
        msgs = self._process_turn(second, first, second_move)
        messages.extend(msgs)

        # Verifier si le premier est KO
        if first.is_fainted():
            messages.append(f"{first.name} est K.O. !")

            loser_player = self.player1 if first == self.pokemon1 else self.player2
            winner_player = self.player2 if loser_player == self.player1 else self.player1

            if not loser_player.has_alive_pokemon():
                self.is_over = True
                self.winner = winner_player
                self.loser = loser_player
                messages.append(f"{winner_player.name} remporte le combat !")
            else:
                messages.append(f"{loser_player.name} doit envoyer un autre Pokemon !")
            return messages

        # Degats de fin de tour (poison, brulure)
        for pokemon in [first, second]:
            if pokemon.status and pokemon.status.is_active:
                msg = pokemon.status.on_turn_end(pokemon)
                if msg:
                    messages.append(msg)
                if not pokemon.status.is_active:
                    pokemon.status = None

                if pokemon.is_fainted():
                    messages.append(f"{pokemon.name} est K.O. !")

                    loser_player = self.player1 if pokemon == self.pokemon1 else self.player2
                    winner_player = self.player2 if loser_player == self.player1 else self.player1

                    if not loser_player.has_alive_pokemon():
                        self.is_over = True
                        self.winner = winner_player
                        self.loser = loser_player
                        messages.append(f"{winner_player.name} remporte le combat !")
                    else:
                        messages.append(f"{loser_player.name} doit envoyer un autre Pokemon !")
                    return messages

        return messages

    def get_fainted_player(self):
        """Retourne le numero du joueur dont le Pokemon actif est KO (1 ou 2), ou None."""
        if self.pokemon1.is_fainted() and self.player1.has_alive_pokemon():
            return 1
        if self.pokemon2.is_fainted() and self.player2.has_alive_pokemon():
            return 2
        return None

    def _determine_order(self, p1, move1, p2, move2):
        """Determine qui attaque en premier selon la vitesse."""
        speed1 = p1.get_effective_speed()
        speed2 = p2.get_effective_speed()

        if speed1 > speed2:
            return p1, move1, p2, move2
        elif speed2 > speed1:
            return p2, move2, p1, move1
        else:
            if random.random() < 0.5:
                return p1, move1, p2, move2
            return p2, move2, p1, move1

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
            return target.apply_status(move.ailment)
        return ""