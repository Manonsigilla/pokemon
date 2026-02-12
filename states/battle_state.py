"""Ecran de combat Pokemon style GBA - Support equipes multi-Pokemon."""

import pygame

from states.state import State
from battle.battle import Battle
from battle.ai import AIOpponent
from ui.hp_bar import HPBar
from ui.text_box import TextBox
from ui.move_menu import MoveMenu
from ui.action_menu import ActionMenu
from ui.team_menu import TeamMenu
from ui.sprite_loader import SpriteLoader
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, PLAYER_SPRITE_POS, ENEMY_SPRITE_POS,
                    PLAYER_INFO_POS, ENEMY_INFO_POS, TEXT_BOX_RECT,
                    MOVE_MENU_RECT, MOVE_TEXT_RECT)


# Phases du combat
PHASE_INTRO = "intro"
PHASE_ACTION_P1 = "action_p1"       # Menu Combat / Pokemon / Fuite (joueur 1)
PHASE_CHOOSE_P1 = "choose_p1"       # Selection attaque joueur 1
PHASE_ACTION_P2 = "action_p2"       # Menu Combat / Pokemon / Fuite (joueur 2)
PHASE_CHOOSE_P2 = "choose_p2"       # Selection attaque joueur 2
PHASE_SWITCH_P1 = "switch_p1"       # Switch volontaire joueur 1
PHASE_SWITCH_P2 = "switch_p2"       # Switch volontaire joueur 2
PHASE_FORCE_SWITCH = "force_switch"  # Switch force apres KO
PHASE_ANIMATE = "animate"
PHASE_RESULT = "result"


class BattleState(State):
    """Gere l'affichage et l'interaction du combat avec equipes."""

    def __init__(self, state_manager, type_chart):
        super().__init__(state_manager)
        self.type_chart = type_chart
        self.battle = None
        self.ai = None
        self.sprite_loader = SpriteLoader()

        self.phase = PHASE_INTRO
        self.hp_bar_p1 = None
        self.hp_bar_p2 = None
        self.text_box = None
        self.move_menu = None
        self.action_menu = None
        self.team_menu = None

        self.player_sprite = None
        self.enemy_sprite = None

        self.message_queue = []
        self.current_message_index = 0

        self.move_p1 = None
        self.move_p2 = None

        # Flash d'attaque
        self.flash_alpha = 0
        self.flash_timer = 0

        # Qui doit switch apres un KO (1 ou 2)
        self._force_switch_player = None
        
        self._fleeing = False # Indique si on est en train de fuir le combat

    def enter(self):
        """Initialise le combat avec les equipes selectionnees."""
        player1 = self.state_manager.shared_data["player1"]
        player2 = self.state_manager.shared_data["player2"]
        mode = self.state_manager.shared_data.get("mode", "pvp")

        # Creer le combat avec les Players
        self.battle = Battle(player1, player2, self.type_chart, battle_type="arena")

        # IA si mode PvIA
        if mode == "pvia":
            self.ai = AIOpponent(self.battle.pokemon2, self.type_chart)
        else:
            self.ai = None

        # Charger les sprites du Pokemon actif
        self._load_sprites()

        # Creer les widgets UI
        self._create_ui()

        # Menus supplementaires
        self.action_menu = ActionMenu(*MOVE_MENU_RECT)
        self.team_menu = TeamMenu()

        # Phase d'intro
        self.phase = PHASE_INTRO
        self.message_queue = [
            f"Combat d'arene : {player1.name} VS {player2.name} !",
            f"{player2.name} envoie {self.battle.pokemon2.name} !",
            f"A toi, {self.battle.pokemon1.name} !",
        ]
        self.current_message_index = 0
        self.text_box.set_text(self.message_queue[0])

        self.move_p1 = None
        self.move_p2 = None
        self._force_switch_player = None
        self._fleeing = False

    def _load_sprites(self):
        """Charge les sprites des Pokemon actifs."""
        self.player_sprite = self.sprite_loader.load_sprite(
            self.battle.pokemon1.back_sprite_path
        )
        self.enemy_sprite = self.sprite_loader.load_sprite(
            self.battle.pokemon2.front_sprite_path
        )

    def _create_ui(self):
        """Cree les widgets UI pour les Pokemon actifs."""
        self.hp_bar_p2 = HPBar(
            ENEMY_INFO_POS[0], ENEMY_INFO_POS[1],
            250, self.battle.pokemon2, show_hp_text=False
        )
        self.hp_bar_p1 = HPBar(
            PLAYER_INFO_POS[0], PLAYER_INFO_POS[1],
            250, self.battle.pokemon1, show_hp_text=True
        )
        self.text_box = TextBox(*TEXT_BOX_RECT)
        self.move_menu = MoveMenu(*MOVE_MENU_RECT, self.battle.pokemon1.moves)

    def _refresh_ui_after_switch(self, player_num):
        """Met a jour les sprites et barres de vie apres un switch."""
        if player_num == 1:
            self.player_sprite = self.sprite_loader.load_sprite(
                self.battle.pokemon1.back_sprite_path
            )
            self.hp_bar_p1 = HPBar(
                PLAYER_INFO_POS[0], PLAYER_INFO_POS[1],
                250, self.battle.pokemon1, show_hp_text=True
            )
        else:
            self.enemy_sprite = self.sprite_loader.load_sprite(
                self.battle.pokemon2.front_sprite_path
            )
            self.hp_bar_p2 = HPBar(
                ENEMY_INFO_POS[0], ENEMY_INFO_POS[1],
                250, self.battle.pokemon2, show_hp_text=False
            )
            # Mettre a jour l'IA si necessaire
            if self.ai:
                self.ai = AIOpponent(self.battle.pokemon2, self.type_chart)

    # =========================================================================
    # GESTION DES EVENEMENTS
    # =========================================================================

    def handle_events(self, events):
        """Gere les inputs selon la phase courante."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Le team menu a priorite quand il est ouvert
                if self.team_menu.visible:
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
                elif self.phase == PHASE_RESULT:
                    self._handle_result(event)

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
                    # Verifier si on etait en train de fuir
                    if getattr(self, '_fleeing', False):
                        self._fleeing = False
                        self.state_manager.change_state("title")
                        return

                    if self.battle.is_over:
                        self.phase = PHASE_RESULT
                        self.text_box.set_text("Appuyez sur Entree pour continuer...")
                    else:
                        # Verifier si un Pokemon est KO et doit etre remplace
                        fainted_player = self.battle.get_fainted_player()
                        if fainted_player is not None:
                            self._force_switch_player = fainted_player
                            self._open_force_switch(fainted_player)
                        else:
                            self._enter_action_phase()

    # --- Menu d'action principal ---

    def _enter_action_phase(self):
        """Affiche le menu Combat / Pokemon / Fuite pour le joueur 1."""
        self.phase = PHASE_ACTION_P1
        self.action_menu.selected_index = 0
        self.action_menu.visible = True
        self.move_menu.visible = False
        self.move_p1 = None
        self.move_p2 = None
        self.text_box.set_text(f"Que doit faire {self.battle.pokemon1.name} ?")

    def _handle_action_p1(self, event):
        """Joueur 1 choisit une action avec WASD + Espace."""
        if event.key == pygame.K_w:
            self.action_menu.navigate("up")
        elif event.key == pygame.K_s:
            self.action_menu.navigate("down")
        elif event.key == pygame.K_SPACE:
            action = self.action_menu.get_selected_action()
            self.action_menu.visible = False

            if action == "combat":
                # Passer au menu d'attaques
                self.phase = PHASE_CHOOSE_P1
                self.move_menu.moves = self.battle.pokemon1.moves
                self.move_menu.selected_index = 0
                self.move_menu.visible = True
            elif action == "pokemon":
                # Ouvrir le menu d'equipe pour switch volontaire
                self.phase = PHASE_SWITCH_P1
                switchable = self.battle.player1.get_switchable_pokemon(self.battle.pokemon1)
                if switchable:
                    self.team_menu.open(
                        self.battle.player1.team,
                        current_pokemon=self.battle.pokemon1,
                        allow_cancel=True
                    )
                else:
                    # Pas de Pokemon dispo pour switch
                    self._show_messages(["Aucun autre Pokemon disponible !"])
            elif action == "fuite":
                # En arene on ne peut pas fuir
                if self.battle.battle_type == "arena":
                    self._show_messages(["Impossible de fuir un combat d'arene !"])
                else:
                    # Futur: gerer la fuite en combat sauvage
                    self._flee_batlle()

    # --- Selection d'attaque Joueur 1 ---

    def _handle_choose_p1(self, event):
        """Joueur 1 choisit une attaque avec WASD + Espace."""
        if event.key == pygame.K_w:
            self.move_menu.navigate("up")
        elif event.key == pygame.K_s:
            self.move_menu.navigate("down")
        elif event.key == pygame.K_a:
            self.move_menu.navigate("left")
        elif event.key == pygame.K_d:
            self.move_menu.navigate("right")
        elif event.key == pygame.K_ESCAPE:
            # Retour au menu d'action
            self.move_menu.visible = False
            self._enter_action_phase()
        elif event.key == pygame.K_SPACE:
            move = self.move_menu.get_selected_move()
            if move.has_pp():
                self.move_p1 = move
                self.move_menu.visible = False

                if self.ai:
                    # L'IA choisit automatiquement
                    self.move_p2 = self.ai.choose_move(self.battle.pokemon1)
                    self._execute_turn()
                else:
                    # Passer au joueur 2 : menu d'action
                    self._enter_action_p2()

    # --- Menu d'action Joueur 2 (PvP) ---

    def _enter_action_p2(self):
        """Affiche le menu d'action pour le joueur 2."""
        self.phase = PHASE_ACTION_P2
        self.action_menu.selected_index = 0
        self.action_menu.visible = True
        self.move_menu.visible = False
        self.text_box.set_text(f"Que doit faire {self.battle.pokemon2.name} ?")

    def _handle_action_p2(self, event):
        """Joueur 2 choisit une action avec Fleches + Entree."""
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

    # --- Selection d'attaque Joueur 2 ---

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
            # Retour au menu d'action P2
            self.move_menu.visible = False
            self._enter_action_p2()
        elif event.key == pygame.K_RETURN:
            move = self.move_menu.get_selected_move()
            if move.has_pp():
                self.move_p2 = move
                self.move_menu.visible = False
                self._execute_turn()

    def _flee_battle(self):
        """Gere la fuite du combat (futur: combat sauvage uniquement)."""
        self._fleeing = True
        self._show_messages(["Vous prenez la fuite !"])
        
    # --- Menu d'equipe (switch) ---

    def _handle_team_menu(self, event):
        """Gere les inputs dans le menu d'equipe."""
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
                # Retour au menu d'action
                if self.phase == PHASE_SWITCH_P1:
                    self._enter_action_phase()
                elif self.phase == PHASE_SWITCH_P2:
                    self._enter_action_p2()
            # Si force_switch, on ne peut pas annuler

    def _perform_switch(self, new_pokemon):
        """Execute le switch et continue le combat."""
        if self.phase == PHASE_SWITCH_P1:
            # Switch volontaire P1 : l'adversaire attaque pendant le switch
            messages = self.battle.switch_pokemon(1, new_pokemon)
            self._refresh_ui_after_switch(1)

            if self.ai:
                self.move_p2 = self.ai.choose_move(self.battle.pokemon1)
                # L'adversaire attaque le nouveau Pokemon
                msgs_attack = self.battle._process_turn(
                    self.battle.pokemon2, self.battle.pokemon1, self.move_p2
                )
                self.move_p2.use()  # Le move.use() est deja appele dans _process_turn
                messages.extend(msgs_attack)

                # Verifier KO du nouveau Pokemon
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
            # Apres animation, execute le tour

        elif self.phase == PHASE_FORCE_SWITCH:
            # Switch force apres KO
            player_num = self._force_switch_player
            messages = self.battle.switch_pokemon(player_num, new_pokemon)
            self._refresh_ui_after_switch(player_num)
            self._force_switch_player = None
            self._show_messages(messages)

    def _open_force_switch(self, player_num):
        """Ouvre le menu de switch force apres un KO."""
        self.phase = PHASE_FORCE_SWITCH
        self._force_switch_player = player_num

        if player_num == 2 and self.ai:
            # L'IA choisit automatiquement le meilleur Pokemon restant
            alive = self.battle.player2.get_alive_pokemon()
            if alive:
                # Choisir le Pokemon avec le plus de PV
                best = max(alive, key=lambda p: p.current_hp)
                messages = self.battle.switch_pokemon(2, best)
                self._refresh_ui_after_switch(2)
                self._show_messages(messages)
            return

        # Joueur humain : ouvrir le menu
        player = self.battle.player1 if player_num == 1 else self.battle.player2
        current = self.battle.pokemon1 if player_num == 1 else self.battle.pokemon2
        self.team_menu.open(
            player.team,
            current_pokemon=current,
            allow_cancel=False  # Pas le choix, il FAUT switch
        )

    # --- Resultat ---

    def _handle_result(self, event):
        """Gere l'ecran de resultat."""
        if event.key == pygame.K_RETURN:
            self.state_manager.shared_data["winner_player"] = self.battle.winner
            self.state_manager.shared_data["loser_player"] = self.battle.loser
            # Garder la compatibilite avec le ResultState existant
            if self.battle.winner:
                self.state_manager.shared_data["winner"] = self.battle.winner.get_active_pokemon() or self.battle.winner.team[0]
                self.state_manager.shared_data["loser"] = self.battle.loser.get_active_pokemon() or self.battle.loser.team[0]
            self.state_manager.change_state("result")

    # =========================================================================
    # EXECUTION DU TOUR
    # =========================================================================

    def _execute_turn(self):
        """Execute le tour et affiche les messages."""
        messages = self.battle.execute_turn(self.move_p1, self.move_p2)
        self._show_messages(messages)

        # Flash d'attaque
        self.flash_alpha = 180
        self.flash_timer = 0.15

    def _show_messages(self, messages):
        """Affiche une liste de messages dans la text box."""
        self.message_queue = messages
        self.current_message_index = 0
        self.phase = PHASE_ANIMATE

        if messages:
            self.text_box.set_text(messages[0])

    # =========================================================================
    # UPDATE & DRAW
    # =========================================================================

    def update(self, dt):
        """Met a jour les animations."""
        self.text_box.update(dt)
        self.hp_bar_p1.update(dt)
        self.hp_bar_p2.update(dt)

        # Flash d'attaque
        if self.flash_timer > 0:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.flash_alpha = 0

    def draw(self, surface):
        """Dessine l'ecran de combat complet."""
        # Fond de l'arene
        self._draw_background(surface)

        # Sprites des Pokemon
        if self.player_sprite:
            surface.blit(self.player_sprite, PLAYER_SPRITE_POS)
        if self.enemy_sprite:
            surface.blit(self.enemy_sprite, ENEMY_SPRITE_POS)

        # Barres de vie
        self.hp_bar_p1.draw(surface)
        self.hp_bar_p2.draw(surface)

        # Indicateurs d'equipe (petites pokeballs)
        self._draw_team_indicators(surface)

        # Zone de texte / menus
        if self.action_menu and self.action_menu.visible:
            # Menu d'action a droite + texte a gauche
            action_box = TextBox(*MOVE_TEXT_RECT)
            if self.phase == PHASE_ACTION_P1:
                action_box.set_text(f"Que doit faire {self.battle.pokemon1.name} ?")
            else:
                action_box.set_text(f"Que doit faire {self.battle.pokemon2.name} ?")
            action_box.skip_animation()
            action_box.draw(surface)
            self.action_menu.draw(surface)

            # Controles
            if self.phase == PHASE_ACTION_P1:
                controls = "W/S + Espace"
            else:
                controls = "Haut/Bas + Entree"
            ctrl_font = pygame.font.Font(None, 18)
            ctrl_text = ctrl_font.render(controls, True, (100, 100, 100))
            surface.blit(ctrl_text, (10, SCREEN_HEIGHT - 18))

        elif self.move_menu and self.move_menu.visible:
            action_box = TextBox(*MOVE_TEXT_RECT)
            if self.phase == PHASE_CHOOSE_P1:
                action_box.set_text(f"Que doit faire {self.battle.pokemon1.name} ?")
            else:
                action_box.set_text(f"Que doit faire {self.battle.pokemon2.name} ?")
            action_box.skip_animation()
            action_box.draw(surface)
            self.move_menu.draw(surface)

            if self.phase == PHASE_CHOOSE_P1:
                controls = "WASD + Espace | Echap = retour"
            else:
                controls = "Fleches + Entree | Echap = retour"
            ctrl_font = pygame.font.Font(None, 18)
            ctrl_text = ctrl_font.render(controls, True, (100, 100, 100))
            surface.blit(ctrl_text, (10, SCREEN_HEIGHT - 18))
        else:
            self.text_box.draw(surface)

        # Flash d'attaque
        if self.flash_alpha > 0:
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surface.fill(WHITE)
            flash_surface.set_alpha(int(self.flash_alpha))
            surface.blit(flash_surface, (0, 0))

        # Team menu en overlay (par dessus tout)
        if self.team_menu and self.team_menu.visible:
            self.team_menu.draw(surface)

    def _draw_team_indicators(self, surface):
        """Dessine des indicateurs pour chaque Pokemon de l'equipe (style pokeball)."""
        indicator_size = 10
        spacing = 16

        # Equipe du joueur 1 (en bas a gauche, au-dessus de la plateforme)
        start_x_p1 = 50
        y_p1 = 415

        for i, poke in enumerate(self.battle.player1.team):
            x = start_x_p1 + i * spacing
            if poke.is_fainted():
                color = (100, 40, 40)  # Rouge sombre = KO
            elif poke == self.battle.pokemon1:
                color = (60, 200, 60)  # Vert = actif
            else:
                color = (200, 200, 200)  # Gris = en reserve
            pygame.draw.circle(surface, color, (x, y_p1), indicator_size // 2)
            pygame.draw.circle(surface, (50, 50, 50), (x, y_p1), indicator_size // 2, 1)

        # Equipe du joueur 2 (en haut a droite, au-dessus de la plateforme)
        start_x_p2 = 680
        y_p2 = 225

        for i, poke in enumerate(self.battle.player2.team):
            x = start_x_p2 + i * spacing
            if poke.is_fainted():
                color = (100, 40, 40)
            elif poke == self.battle.pokemon2:
                color = (60, 200, 60)
            else:
                color = (200, 200, 200)
            pygame.draw.circle(surface, color, (x, y_p2), indicator_size // 2)
            pygame.draw.circle(surface, (50, 50, 50), (x, y_p2), indicator_size // 2, 1)

    def _draw_background(self, surface):
        """Dessine le fond de l'arene style GBA."""
        # Ciel
        surface.fill((136, 192, 240))

        # Sol (plateforme adverse)
        pygame.draw.ellipse(
            surface, (144, 200, 120),
            (420, 230, 320, 60)
        )
        pygame.draw.ellipse(
            surface, (120, 176, 100),
            (420, 230, 320, 60), 2
        )

        # Sol (plateforme joueur)
        pygame.draw.ellipse(
            surface, (144, 200, 120),
            (20, 420, 350, 70)
        )
        pygame.draw.ellipse(
            surface, (120, 176, 100),
            (20, 420, 350, 70), 2
        )

        # Ligne de sol
        pygame.draw.rect(surface, (120, 176, 100), (0, 430, SCREEN_WIDTH, 170))