"""Ecran titre / menu principal."""

import pygame

from states.state import State
from ui.button import Button
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE,
                    BG_DARK, YELLOW, RED, BLUE, get_font)


class TitleState(State):
    """Menu principal avec selection du mode de jeu."""

    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.buttons = []
        self._title_font = None
        self._subtitle_font = None

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
        center_x = SCREEN_WIDTH // 2
        btn_width = 300
        btn_height = 60

        self.buttons = [
            Button(
                center_x - btn_width // 2, 320,
                btn_width, btn_height,
                "Joueur vs Joueur"
            ),
            Button(
                center_x - btn_width // 2, 400,
                btn_width, btn_height,
                "Joueur vs IA"
            ),
        ]

    def handle_events(self, events):
        """Detecte les clics sur les boutons."""
        mouse_pos = pygame.mouse.get_pos()

        for button in self.buttons:
            button.check_hover(mouse_pos)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.buttons[0].check_click(mouse_pos, True):
                    self.state_manager.shared_data["mode"] = "pvp"
                    self.state_manager.change_state("selection")
                elif self.buttons[1].check_click(mouse_pos, True):
                    self.state_manager.shared_data["mode"] = "pvia"
                    self.state_manager.change_state("selection")

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.state_manager.shared_data["mode"] = "pvp"
                    self.state_manager.change_state("selection")
                elif event.key == pygame.K_2:
                    self.state_manager.shared_data["mode"] = "pvia"
                    self.state_manager.change_state("selection")

    def update(self, dt):
        pass

    def draw(self, surface):
        """Dessine le menu principal."""
        surface.fill(BG_DARK)

        # Titre
        title = self.title_font.render("POKEMON", True, YELLOW)
        title2 = self.title_font.render("BATTLE ARENA", True, RED)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        title2_x = (SCREEN_WIDTH - title2.get_width()) // 2
        surface.blit(title, (title_x, 100))
        surface.blit(title2, (title2_x, 160))

        # Sous-titre
        subtitle = self.subtitle_font.render("Choisissez votre mode de jeu", True, WHITE)
        sub_x = (SCREEN_WIDTH - subtitle.get_width()) // 2
        surface.blit(subtitle, (sub_x, 270))

        # Boutons
        for button in self.buttons:
            button.draw(surface)

        # Instructions
        hint = self.subtitle_font.render("ou appuyez sur 1 / 2", True, (180, 180, 180))
        hint_x = (SCREEN_WIDTH - hint.get_width()) // 2
        surface.blit(hint, (hint_x, 500))