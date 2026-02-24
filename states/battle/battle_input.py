"""Mixin de gestion des inputs pour l'ecran de combat."""

import pygame

from battle.ai import AI_SWITCH
from ui.sound_manager import sound_manager

from states.battle.constants import (
    PHASE_INTRO, PHASE_ACTION_P1, PHASE_CHOOSE_P1,
    PHASE_ACTION_P2, PHASE_CHOOSE_P2,
    PHASE_SWITCH_P1, PHASE_SWITCH_P2, PHASE_FORCE_SWITCH,
    PHASE_ANIMATE, PHASE_SHOW_RESULTS, PHASE_RESULT
)


class BattleInput:
    """Methodes de gestion des evenements du combat."""

    def handle_events(self, events):
        """Gere les inputs selon la phase courante."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Manon : le team menu a priorite quand il est ouvert
                if self.team_menu and self.team_menu.visible:
                    self._handle_team_menu(event)
                    return

                if self.phase == PHASE_INTRO:
                    self._handle_message_advance(event)

                elif self.phase == PHASE_ACTION_P1:
                    self._handle_action_p1(event)

                elif self.phase == PHASE_CHOOSE_P1:
                    self._handle_choose_p1(event)

                elif self.phase == PHASE_ACTION_P2:
                    self._handle_action_p2(event)

                elif self.phase == PHASE_CHOOSE_P2:
                    self._handle_choose_p2(event)

                elif self.phase == PHASE_ANIMATE:
                    self._handle_message_advance(event)

                elif self.phase == PHASE_SHOW_RESULTS:
                    self._handle_results_input(event)

                elif self.phase == PHASE_RESULT:
                    self._handle_result(event)
                # Note: PHASE_EXECUTE_ANIMATION n'a pas d'input, c'est automatique

    def _handle_message_advance(self, event):
        """Avance dans la file de messages."""
        if event.key in (pygame.K_SPACE, pygame.K_RETURN):
            if not self.text_box.is_complete:
                self.text_box.skip_animation()
                return

            self.current_message_index += 1
            if self.current_message_index < len(self.message_queue):
                self.text_box.set_text(self.message_queue[self.current_message_index])
            else:
                # Fin des messages
                if self.phase == PHASE_INTRO:
                    self._enter_action_phase()
                elif self.phase == PHASE_ANIMATE:
                    # Manon : verifier fuite
                    if self._fleeing:
                        self._fleeing = False
                        if self.state_manager.shared_data.pop("adventure_return", False):
                            self.state_manager.change_state("map")
                        else:
                            self.state_manager.change_state("title")
                        return

                    if self.battle.is_over:
                        self.phase = PHASE_RESULT
                        self.text_box.set_text("Appuyez sur Entree pour continuer...")
                    else:
                        # Manon : verifier si un Pokemon est KO et doit etre remplace
                        fainted = self.battle.get_fainted_player()
                        if fainted is not None:
                            self._open_force_switch(fainted)
                        else:
                            self._enter_action_phase()

    def _handle_action_p1(self, event):
        """Joueur 1 choisit une action avec Fleches + Entree."""
        if event.key in (pygame.K_UP, pygame.K_w):
            self.action_menu.navigate("up")
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.action_menu.navigate("down")
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            action = self.action_menu.get_selected_action()
            self.action_menu.visible = False

            if action == "combat":
                self.phase = PHASE_CHOOSE_P1
                self.move_menu.moves = self.battle.pokemon1.moves
                self.move_menu.selected_index = 0
                self.move_menu.visible = True
            elif action == "pokemon":
                self.phase = PHASE_SWITCH_P1
                switchable = self.battle.player1.get_switchable_pokemon(self.battle.pokemon1)
                if switchable:
                    self.team_menu.open(
                        self.battle.player1.team,
                        current_pokemon=self.battle.pokemon1,
                        allow_cancel=True
                    )
                else:
                    self._show_messages(["Aucun autre Pokemon disponible !"])
            elif action == "fuite":
                if self.battle.battle_type == "arena":
                    self._show_messages(["Impossible de fuir un combat d'arene !"])
                else:
                    self._flee_battle()

    def _handle_choose_p1(self, event):
        """Joueur 1 choisit une attaque avec Fleches + Entree."""
        if event.key in (pygame.K_UP, pygame.K_w):
            self.move_menu.navigate("up")
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.move_menu.navigate("down")
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.move_menu.navigate("left")
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.move_menu.navigate("right")
        elif event.key == pygame.K_ESCAPE:
            self.move_menu.visible = False
            self._enter_action_phase()
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            move = self.move_menu.get_selected_move()
            if move.has_pp():
                self.move_p1 = move
                self.move_menu.visible = False

                if self.ai:
                    # L'IA choisit automatiquement (peut decider de switcher)
                    switchable = self.battle.player2.get_switchable_pokemon(
                        self.battle.pokemon2
                    )
                    action, switch_target = self.ai.choose_action(
                        self.battle.pokemon1, switchable
                    )

                    if action == AI_SWITCH and switch_target:
                        # L'IA decide de switcher volontairement
                        messages = self.battle.switch_pokemon(2, switch_target)
                        self._refresh_ui_after_switch(2)
                        # Le joueur attaque le nouveau Pokemon
                        msgs_attack = self.battle._process_turn(
                            self.battle.pokemon1, self.battle.pokemon2, self.move_p1
                        )
                        self.move_p1.use()
                        messages.extend(msgs_attack)
                        if self.battle.pokemon2.is_fainted():
                            messages.append(f"{self.battle.pokemon2.name} est K.O. !")
                            if not self.battle.player2.has_alive_pokemon():
                                self.battle.is_over = True
                                self.battle.winner = self.battle.player1
                                self.battle.loser = self.battle.player2
                                messages.append(
                                    f"{self.battle.player1.name} remporte le combat !"
                                )
                        self._show_messages(messages)
                    else:
                        self.move_p2 = action
                        # Angie : determiner l'ordre et lancer les animations
                        self._determine_turn_order()
                        self._execute_next_attack()
                else:
                    # Manon : passer au joueur 2 - menu d'action
                    self._enter_action_p2()

    def _handle_action_p2(self, event):
        """Manon : Joueur 2 choisit une action avec Fleches + Entree."""
        if event.key == pygame.K_UP:
            self.action_menu.navigate("up")
        elif event.key == pygame.K_DOWN:
            self.action_menu.navigate("down")
        elif event.key == pygame.K_RETURN:
            action = self.action_menu.get_selected_action()
            self.action_menu.visible = False

            if action == "combat":
                self.phase = PHASE_CHOOSE_P2
                self.move_menu.moves = self.battle.pokemon2.moves
                self.move_menu.selected_index = 0
                self.move_menu.visible = True
            elif action == "pokemon":
                self.phase = PHASE_SWITCH_P2
                switchable = self.battle.player2.get_switchable_pokemon(self.battle.pokemon2)
                if switchable:
                    self.team_menu.open(
                        self.battle.player2.team,
                        current_pokemon=self.battle.pokemon2,
                        allow_cancel=True
                    )
                else:
                    self._show_messages(["Aucun autre Pokemon disponible !"])
            elif action == "fuite":
                if self.battle.battle_type == "arena":
                    self._show_messages(["Impossible de fuir un combat d'arene !"])
                else:
                    self._flee_battle()

    def _handle_choose_p2(self, event):
        """Joueur 2 choisit une attaque avec Fleches + Entree."""
        if event.key == pygame.K_UP:
            self.move_menu.navigate("up")
        elif event.key == pygame.K_DOWN:
            self.move_menu.navigate("down")
        elif event.key == pygame.K_LEFT:
            self.move_menu.navigate("left")
        elif event.key == pygame.K_RIGHT:
            self.move_menu.navigate("right")
        elif event.key == pygame.K_ESCAPE:
            self.move_menu.visible = False
            self._enter_action_p2()
        elif event.key == pygame.K_RETURN:
            move = self.move_menu.get_selected_move()
            if move.has_pp():
                self.move_p2 = move
                self.move_menu.visible = False
                # Angie : determiner l'ordre et lancer les animations
                self._determine_turn_order()
                self._execute_next_attack()

    def _handle_team_menu(self, event):
        """Manon : Gere les inputs dans le menu d'equipe."""
        if event.key in (pygame.K_UP, pygame.K_w):
            self.team_menu.navigate("up")
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.team_menu.navigate("down")
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            selected = self.team_menu.get_selected_pokemon()
            if selected:
                self.team_menu.close()
                self._perform_switch(selected)
        elif event.key == pygame.K_ESCAPE:
            if self.team_menu.allow_cancel:
                self.team_menu.close()
                if self.phase == PHASE_SWITCH_P1:
                    self._enter_action_phase()
                elif self.phase == PHASE_SWITCH_P2:
                    self._enter_action_p2()
            # Si force_switch, on ne peut pas annuler

    def _handle_results_input(self, event):
        """Angie : Avance dans les messages de resultats."""
        if event.key in (pygame.K_SPACE, pygame.K_RETURN):
            if not self.text_box.is_complete:
                self.text_box.skip_animation()
                return

            self.current_message_index += 1
            if self.current_message_index < len(self.message_queue):
                self.text_box.set_text(self.message_queue[self.current_message_index])
            else:
                # Fin des messages
                if self.battle.is_over:
                    self.phase = PHASE_RESULT
                    self.text_box.set_text("Appuyez sur Entree pour continuer...")
                else:
                    # Manon : verifier si un Pokemon est KO et doit etre remplace
                    fainted = self.battle.get_fainted_player()
                    if fainted is not None:
                        self._open_force_switch(fainted)
                    else:
                        # Passer a l'attaque suivante ou nouveau tour
                        self.current_turn_index += 1
                        self._execute_next_attack()
