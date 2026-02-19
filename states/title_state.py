"""Ecran titre / menu principal."""

import pygame

from states.state import State
from ui.button import Button
from ui.sound_manager import sound_manager
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE,
                    BG_DARK, YELLOW, RED, BLUE, get_font, render_fitted_text)


class TitleState(State):
    """Menu principal avec selection du mode de jeu."""

    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.buttons = []
        self._title_font = None
        self._subtitle_font = None
        self._show_difficulty = False
        self.difficulty_buttons = []

    @property
    def title_font(self):
        if self._title_font is None:
            self._title_font = get_font(32)
        return self._title_font

    @property
    def subtitle_font(self):
        if self._subtitle_font is None:
            self._subtitle_font = get_font(14)
        return self._subtitle_font

    def enter(self):
        """Cree les boutons du menu."""
        sound_manager.play_music("pokemontheme.mp3")
        self._show_difficulty = False
        center_x = SCREEN_WIDTH // 2
        btn_width = 300
        btn_height = 60

        self.buttons = [
            Button(
            center_x - btn_width // 2, 250,
            btn_width, btn_height,
            "Nouvelle Aventure"
            ),
            Button(
                center_x - btn_width // 2, 320,
                btn_width, btn_height,
                "Joueur vs Joueur"
            ),
            Button(
                center_x - btn_width // 2, 390,
                btn_width, btn_height,
                "Joueur vs IA"
            ),
        ]

        # Boutons de difficulte (affiches quand on clique "Joueur vs IA")
        diff_btn_width = 200
        diff_btn_height = 50
        self.difficulty_buttons = [
            Button(
                center_x - diff_btn_width // 2, 300,
                diff_btn_width, diff_btn_height,
                "Facile"
            ),
            Button(
                center_x - diff_btn_width // 2, 370,
                diff_btn_width, diff_btn_height,
                "Normal"
            ),
            Button(
                center_x - diff_btn_width // 2, 440,
                diff_btn_width, diff_btn_height,
                "Difficile"
            ),
        ]

    def handle_events(self, events):
        """Detecte les clics sur les boutons."""
        mouse_pos = pygame.mouse.get_pos()

        if self._show_difficulty:
            for button in self.difficulty_buttons:
                button.check_hover(mouse_pos)
        else:
            for button in self.buttons:
                button.check_hover(mouse_pos)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._show_difficulty:
                    self._handle_difficulty_click(mouse_pos)
                else:
                    if self.buttons[0].check_click(mouse_pos, True):
                        sound_manager.play_select()
                        self.state_manager.change_state("starter_selection")
                    # Joueur vs Joueur
                    elif self.buttons[1].check_click(mouse_pos, True):
                        sound_manager.play_select()
                        self.state_manager.shared_data["mode"] = "pvp"
                        self.state_manager.change_state("selection")
                    # Joueur vs IA
                    elif self.buttons[2].check_click(mouse_pos, True):
                        sound_manager.play_select()
                        self._show_difficulty = True

            if event.type == pygame.KEYDOWN:
                if self._show_difficulty:
                    self._handle_difficulty_key(event)
                else:
                    if event.key == pygame.K_1:
                        sound_manager.play_select()
                        self.state_manager.shared_data["mode"] = "pvp"
                        self.state_manager.change_state("selection")
                    elif event.key == pygame.K_2:
                        sound_manager.play_select()
                        self._show_difficulty = True

    def _handle_difficulty_click(self, mouse_pos):
        """Gere le clic sur un bouton de difficulte."""
        difficulties = ["facile", "normal", "difficile"]
        for i, button in enumerate(self.difficulty_buttons):
            if button.check_click(mouse_pos, True):
                sound_manager.play_select()
                self.state_manager.shared_data["mode"] = "pvia"
                self.state_manager.shared_data["ai_difficulty"] = difficulties[i]
                self.state_manager.change_state("selection")
                return

    def _handle_difficulty_key(self, event):
        """Gere les touches clavier dans le sous-menu difficulte."""
        difficulties = ["facile", "normal", "difficile"]
        key_map = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}

        if event.key in key_map:
            sound_manager.play_select()
            idx = key_map[event.key]
            self.state_manager.shared_data["mode"] = "pvia"
            self.state_manager.shared_data["ai_difficulty"] = difficulties[idx]
            self.state_manager.change_state("selection")
        elif event.key == pygame.K_ESCAPE:
            self._show_difficulty = False

    def update(self, dt):
        pass

    def draw(self, surface):
        """Dessine le menu principal."""
        surface.fill(BG_DARK)

        max_width = SCREEN_WIDTH - 40

        # Titre
        title = render_fitted_text("POKEMON", max_width, 32, YELLOW, min_size=18)
        title2 = render_fitted_text("BATTLE ARENA", max_width, 32, RED, min_size=18)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        title2_x = (SCREEN_WIDTH - title2.get_width()) // 2
        surface.blit(title, (title_x, 100))
        surface.blit(title2, (title2_x, 160))

        if self._show_difficulty:
            # Sous-titre difficulte
            subtitle = render_fitted_text(
                "Choisissez la difficulte", max_width, 14, WHITE, min_size=10
            )
            sub_x = (SCREEN_WIDTH - subtitle.get_width()) // 2
            surface.blit(subtitle, (sub_x, 260))

            # Boutons de difficulte
            for button in self.difficulty_buttons:
                button.draw(surface)

            # Instructions
            hint = render_fitted_text(
                "1 / 2 / 3 ou cliquez | Echap = retour", max_width, 14, (180, 180, 180), min_size=9
            )
            hint_x = (SCREEN_WIDTH - hint.get_width()) // 2
            surface.blit(hint, (hint_x, 520))
        else:
            # Sous-titre
            subtitle = render_fitted_text(
                "Choisissez votre mode de jeu", max_width, 14, WHITE, min_size=10
            )
            sub_x = (SCREEN_WIDTH - subtitle.get_width()) // 2
            surface.blit(subtitle, (sub_x, 270))

            # Boutons
            for button in self.buttons:
                button.draw(surface)

            # Instructions
            hint = render_fitted_text(
                "ou appuyez sur 1 / 2", max_width, 14, (180, 180, 180), min_size=9
            )
            hint_x = (SCREEN_WIDTH - hint.get_width()) // 2
            surface.blit(hint, (hint_x, 500))
