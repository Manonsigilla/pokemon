"""Mixin de logique de combat."""

import random

from battle.ai import AIOpponent
from ui.sound_manager import sound_manager

from states.battle.constants import (
    PHASE_FORCE_SWITCH, PHASE_SWITCH_P1, PHASE_SWITCH_P2,
    PHASE_SHOW_RESULTS, PHASE_RESULT
)
from config import PLAYER_SPRITE_POS, ENEMY_SPRITE_POS


class BattleLogic:
    """Methodes de logique de combat (degats, switch, fin de tour)."""

    def _flee_battle(self):
        """Gere la fuite du combat."""
        sound_manager.play_flee()
        self._fleeing = True
        self._show_messages(["Vous prenez la fuite !"])

    def _perform_switch(self, new_pokemon):
        """Manon : Execute le switch et continue le combat."""
        sound_manager.play_switch()
        if self.phase == PHASE_SWITCH_P1:
            # Switch volontaire P1 : l'adversaire attaque pendant le switch
            messages = self.battle.switch_pokemon(1, new_pokemon)
            self._refresh_ui_after_switch(1)

            if self.ai:
                # L'IA attaque pendant le switch du joueur (pas de switch IA ici)
                self.move_p2 = self.ai.choose_move(self.battle.pokemon1)
                msgs_attack = self.battle._process_turn(
                    self.battle.pokemon2, self.battle.pokemon1, self.move_p2
                )
                messages.extend(msgs_attack)

                if self.battle.pokemon1.is_fainted():
                    messages.append(f"{self.battle.pokemon1.name} est K.O. !")
                    if not self.battle.player1.has_alive_pokemon():
                        self.battle.is_over = True
                        self.battle.winner = self.battle.player2
                        self.battle.loser = self.battle.player1
                        messages.append(f"{self.battle.player2.name} remporte le combat !")

            self._show_messages(messages)

        elif self.phase == PHASE_SWITCH_P2:
            # Switch volontaire P2
            messages = self.battle.switch_pokemon(2, new_pokemon)
            self._refresh_ui_after_switch(2)
            self._show_messages(messages)

        elif self.phase == PHASE_FORCE_SWITCH:
            # Switch force apres KO
            player_num = self._force_switch_player
            messages = self.battle.switch_pokemon(player_num, new_pokemon)
            self._refresh_ui_after_switch(player_num)
            self._force_switch_player = None
            self._show_messages(messages)

    def _determine_turn_order(self):
        """Angie : Determine qui attaque en premier selon la vitesse."""
        p1 = self.battle.pokemon1
        p2 = self.battle.pokemon2

        speed1 = p1.get_effective_speed()
        speed2 = p2.get_effective_speed()

        if speed1 > speed2:
            self.turn_order = [
                (p1, self.move_p1, True),
                (p2, self.move_p2, False)
            ]
        elif speed2 > speed1:
            self.turn_order = [
                (p2, self.move_p2, False),
                (p1, self.move_p1, True)
            ]
        else:
            if random.random() < 0.5:
                self.turn_order = [
                    (p1, self.move_p1, True),
                    (p2, self.move_p2, False)
                ]
            else:
                self.turn_order = [
                    (p2, self.move_p2, False),
                    (p1, self.move_p1, True)
                ]

        self.current_turn_index = 0

    def _apply_attack_damage(self):
        """Angie : Applique les degats et lance les animations d'impact."""
        from battle.animation import ShakeAnimation, ImpactParticles, EffectivenessFlash
        from ui.damage_number import DamageNumber

        attacker, move, is_player = self.turn_order[self.current_turn_index]
        defender = self.battle.pokemon2 if is_player else self.battle.pokemon1

        # Verifier la precision
        if random.randint(1, 100) > move.accuracy:
            self._attack_missed = True
            return

        self._attack_missed = False

        # Calculer les degats
        if move.is_damaging():
            result = self.battle.damage_calc.calculate(attacker, defender, move)
            defender.take_damage(result.damage)

            self._last_result = result

            # Sons d'impact
            if result.effectiveness == 0:
                pass
            elif result.is_critical:
                sound_manager.play_critical()
            elif result.effectiveness >= 2.0:
                sound_manager.play_super_effective()
            elif result.effectiveness < 1.0:
                sound_manager.play_not_effective()
            else:
                sound_manager.play_hit()

            # Position du defenseur pour les animations
            defender_pos = list(ENEMY_SPRITE_POS) if is_player else list(PLAYER_SPRITE_POS)

            # Shake
            self.shake_animation = ShakeAnimation(
                tuple(defender_pos),
                intensity=12 if result.damage > 50 else 8
            )

            # Particules
            particle_pos = (defender_pos[0] + 40, defender_pos[1] + 40)

            if result.effectiveness >= 2.0:
                particle_color = (100, 255, 100)
            elif result.effectiveness < 1.0 and result.effectiveness > 0:
                particle_color = (255, 100, 100)
            else:
                particle_color = (255, 255, 100)

            self.impact_particles.append(ImpactParticles(particle_pos, particle_color))

            # Degats flottants
            dmg_pos = (particle_pos[0], particle_pos[1] - 20)
            self.damage_numbers.append(
                DamageNumber(
                    result.damage,
                    dmg_pos,
                    is_critical=result.is_critical,
                    is_effective=result.effectiveness
                )
            )

            # Flash d'efficacite
            if result.effectiveness != 1.0:
                self.effectiveness_flash = EffectivenessFlash(result.effectiveness)

            # Appliquer le statut
            if move.ailment and result.effectiveness > 0:
                if move.ailment_chance > 0:
                    if random.randint(1, 100) <= move.ailment_chance:
                        defender.apply_status(move.ailment)
        else:
            self._last_result = None

    def _show_attack_results(self):
        """Angie : Affiche les messages de resultat de l'attaque."""
        attacker, move, is_player = self.turn_order[self.current_turn_index]
        defender = self.battle.pokemon2 if is_player else self.battle.pokemon1

        messages = []

        if self._attack_missed:
            messages.append(f"L'attaque de {attacker.name} a echoue !")
        elif self._last_result:
            result = self._last_result

            if result.effectiveness == 0:
                messages.append("Ca n'a aucun effet...")
            else:
                messages.append(f"{defender.name} perd {result.damage} PV !")

                eff_text = self.type_chart.get_effectiveness_text(result.effectiveness)
                if eff_text:
                    messages.append(eff_text)

                if result.is_critical:
                    messages.append("Coup critique !")

        # Manon : verifier KO avec systeme d'equipes
        if defender.is_fainted():
            sound_manager.play_ko()
            messages.append(f"{defender.name} est K.O. !")

            # Determiner le Player perdant
            loser_player = self.battle.player2 if defender == self.battle.pokemon2 else self.battle.player1
            winner_player = self.battle.player1 if loser_player == self.battle.player2 else self.battle.player2

            if not loser_player.has_alive_pokemon():
                self.battle.is_over = True
                self.battle.winner = winner_player
                self.battle.loser = loser_player
                messages.append(f"{winner_player.name} remporte le combat !")
            else:
                messages.append(f"{loser_player.name} doit envoyer un autre Pokemon !")

        if messages:
            self.message_queue = messages
            self.current_message_index = 0
            self.text_box.set_text(messages[0])
            self.phase = PHASE_SHOW_RESULTS
        else:
            self.current_turn_index += 1
            self._execute_next_attack()

    def _end_turn(self):
        """Angie : Termine le tour et verifie les effets de statut."""
        messages = []

        for pokemon in [self.battle.pokemon1, self.battle.pokemon2]:
            if pokemon.status and pokemon.status.is_active:
                msg = pokemon.status.on_turn_end(pokemon)
                if msg:
                    messages.append(msg)
                if not pokemon.status.is_active:
                    pokemon.status = None

                if pokemon.is_fainted():
                    messages.append(f"{pokemon.name} est K.O. !")

                    # Manon : determiner le Player perdant
                    loser_player = self.battle.player1 if pokemon == self.battle.pokemon1 else self.battle.player2
                    winner_player = self.battle.player2 if loser_player == self.battle.player1 else self.battle.player1

                    if not loser_player.has_alive_pokemon():
                        self.battle.is_over = True
                        self.battle.winner = winner_player
                        self.battle.loser = loser_player
                        messages.append(f"{winner_player.name} remporte le combat !")
                    else:
                        messages.append(f"{loser_player.name} doit envoyer un autre Pokemon !")
                    break

        if messages:
            self.message_queue = messages
            self.current_message_index = 0
            self.text_box.set_text(messages[0])
            self.phase = PHASE_SHOW_RESULTS
        else:
            self._enter_action_phase()
