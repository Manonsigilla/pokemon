"""Ecran de combat Pokemon style GBA."""

import random
import pygame

from states.state import State
from battle.battle import Battle
from battle.ai import AIOpponent
from ui.hp_bar import HPBar
from ui.text_box import TextBox
from ui.move_menu import MoveMenu
from ui.sprite_loader import SpriteLoader
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, BG_LIGHT,
                    BORDER_COLOR, PLAYER_SPRITE_POS, ENEMY_SPRITE_POS,
                    PLAYER_INFO_POS, ENEMY_INFO_POS, TEXT_BOX_RECT,
                    MOVE_MENU_RECT, MOVE_TEXT_RECT, YELLOW,
                    ARENA_BACKGROUNDS, GAME_FONT)


# Phases du combat
PHASE_INTRO = "intro"
PHASE_CHOOSE_P1 = "choose_p1"
PHASE_CHOOSE_P2 = "choose_p2"
PHASE_ANIMATE = "animate"
PHASE_RESULT = "result"


class BattleState(State):
    """Gere l'affichage et l'interaction du combat."""

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

        self.player_sprite = None
        self.enemy_sprite = None

        self.message_queue = []
        self.current_message_index = 0

        self.move_p1 = None
        self.move_p2 = None

        # Fond d'arene
        self.background_image = None

        # Flash d'attaque
        self.flash_alpha = 0
        self.flash_timer = 0

        self._font_action = None

    @property
    def font_action(self):
        if self._font_action is None:
            self._font_action = pygame.font.Font(GAME_FONT, 22) if GAME_FONT else pygame.font.Font(None, 28)
        return self._font_action

    def enter(self):
        """Initialise le combat avec les Pokemon selectionnes."""
        pokemon1 = self.state_manager.shared_data["pokemon1"]
        pokemon2 = self.state_manager.shared_data["pokemon2"]
        mode = self.state_manager.shared_data.get("mode", "pvp")

        # Creer le combat
        self.battle = Battle(pokemon1, pokemon2, self.type_chart)

        # IA si mode PvIA
        if mode == "pvia":
            self.ai = AIOpponent(pokemon2, self.type_chart)
        else:
            self.ai = None

        # Charger le fond d'arene aleatoire
        arena_path = random.choice(ARENA_BACKGROUNDS)
        bg = pygame.image.load(arena_path).convert()
        self.background_image = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

        # Charger les sprites
        self.player_sprite = self.sprite_loader.load_sprite(pokemon1.back_sprite_path)
        self.enemy_sprite = self.sprite_loader.load_sprite(pokemon2.front_sprite_path)

        # Creer les widgets UI
        self.hp_bar_p2 = HPBar(
            ENEMY_INFO_POS[0], ENEMY_INFO_POS[1],
            250, pokemon2, show_hp_text=False
        )
        self.hp_bar_p1 = HPBar(
            PLAYER_INFO_POS[0], PLAYER_INFO_POS[1],
            250, pokemon1, show_hp_text=True
        )

        self.text_box = TextBox(*TEXT_BOX_RECT)
        self.move_menu = MoveMenu(*MOVE_MENU_RECT, pokemon1.moves)

        # Phase d'intro
        self.phase = PHASE_INTRO
        self.message_queue = [
            f"Un combat commence !",
            f"{pokemon2.name} entre en scene !",
            f"A toi, {pokemon1.name} !",
        ]
        self.current_message_index = 0
        self.text_box.set_text(self.message_queue[0])

        self.move_p1 = None
        self.move_p2 = None

    def handle_events(self, events):
        """Gere les inputs selon la phase courante."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.phase == PHASE_INTRO:
                    self._handle_message_advance(event)

                elif self.phase == PHASE_CHOOSE_P1:
                    self._handle_choose_p1(event)

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
                    self._enter_choose_phase()
                elif self.phase == PHASE_ANIMATE:
                    if self.battle.is_over:
                        self.phase = PHASE_RESULT
                        self.text_box.set_text("Appuyez sur Entree pour continuer...")
                    else:
                        self._enter_choose_phase()

    def _enter_choose_phase(self):
        """Passe a la phase de selection du move du joueur 1."""
        self.phase = PHASE_CHOOSE_P1
        self.move_menu.moves = self.battle.pokemon1.moves
        self.move_menu.selected_index = 0
        self.move_menu.visible = True
        self.move_p1 = None
        self.move_p2 = None
        self.text_box.set_text(f"Que doit faire {self.battle.pokemon1.name} ?")

    def _handle_choose_p1(self, event):
        """Joueur 1 choisit avec WASD + Espace."""
        if event.key == pygame.K_w:
            self.move_menu.navigate("up")
        elif event.key == pygame.K_s:
            self.move_menu.navigate("down")
        elif event.key == pygame.K_a:
            self.move_menu.navigate("left")
        elif event.key == pygame.K_d:
            self.move_menu.navigate("right")
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
                    # Passer au joueur 2
                    self.phase = PHASE_CHOOSE_P2
                    self.move_menu.moves = self.battle.pokemon2.moves
                    self.move_menu.selected_index = 0
                    self.move_menu.visible = True
                    self.text_box.set_text(f"Que doit faire {self.battle.pokemon2.name} ?")

    def _handle_choose_p2(self, event):
        """Joueur 2 choisit avec fleches + Entree."""
        if event.key == pygame.K_UP:
            self.move_menu.navigate("up")
        elif event.key == pygame.K_DOWN:
            self.move_menu.navigate("down")
        elif event.key == pygame.K_LEFT:
            self.move_menu.navigate("left")
        elif event.key == pygame.K_RIGHT:
            self.move_menu.navigate("right")
        elif event.key == pygame.K_RETURN:
            move = self.move_menu.get_selected_move()
            if move.has_pp():
                self.move_p2 = move
                self.move_menu.visible = False
                self._execute_turn()

    def _handle_result(self, event):
        """Gere l'ecran de resultat."""
        if event.key == pygame.K_RETURN:
            self.state_manager.shared_data["winner"] = self.battle.winner
            self.state_manager.shared_data["loser"] = self.battle.loser
            self.state_manager.change_state("result")

    def _execute_turn(self):
        """Execute le tour et affiche les messages."""
        messages = self.battle.execute_turn(self.move_p1, self.move_p2)
        self.message_queue = messages
        self.current_message_index = 0
        self.phase = PHASE_ANIMATE

        if messages:
            self.text_box.set_text(messages[0])

        # Flash d'attaque
        self.flash_alpha = 180
        self.flash_timer = 0.15

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

        # Zone de texte / menu
        if self.move_menu.visible:
            # Afficher le texte d'action a gauche et le menu a droite
            action_box = TextBox(*MOVE_TEXT_RECT)
            if self.phase == PHASE_CHOOSE_P1:
                action_box.set_text(f"Que doit faire {self.battle.pokemon1.name} ?")
            else:
                action_box.set_text(f"Que doit faire {self.battle.pokemon2.name} ?")
            action_box.skip_animation()
            action_box.draw(surface)
            self.move_menu.draw(surface)

            # Indicateur de controles
            if self.phase == PHASE_CHOOSE_P1:
                controls = "WASD + Espace"
            else:
                controls = "Fleches + Entree"
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

    def _draw_background(self, surface):
        """Dessine le fond de l'arene avec l'image chargee."""
        if self.background_image:
            surface.blit(self.background_image, (0, 0))
        else:
            surface.fill((136, 192, 240))
