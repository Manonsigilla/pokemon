"""Ecran titre / menu principal."""

import pygame

from states.state import State
from ui.button import Button
from ui.sound_manager import sound_manager
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE,
                    BG_DARK, YELLOW, RED, BLUE, get_font,
                    TITLE_LOGO, BG_MENU,
                    BTN_AVENTURE, BTN_AVENTURE_HOVER,
                    BTN_PVP, BTN_PVP_HOVER,
                    BTN_IA, BTN_IA_HOVER,
                    BTN_FACILE, BTN_FACILE_HOVER,
                    BTN_NORMAL, BTN_NORMAL_HOVER,
                    BTN_DIFFICILE, BTN_DIFFICILE_HOVER)


class TitleState(State):
    """Menu principal avec selection du mode de jeu."""

    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.buttons = []
        self._title_font = None
        self._subtitle_font = None
        self._show_difficulty = False
        self.difficulty_buttons = []
        self.logo_image = None
        self.bg_image = None

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

        # ============ FOND ============
        try:
            bg = pygame.image.load(BG_MENU).convert()
            self.bg_image = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            self.bg_image = None

        # ============ LOGO ============
        try:
            logo = pygame.image.load(TITLE_LOGO).convert_alpha()
            max_logo_width = 600
            ratio = min(max_logo_width / logo.get_width(), 1.0)
            new_w = int(logo.get_width() * ratio)
            new_h = int(logo.get_height() * ratio)
            self.logo_image = pygame.transform.scale(logo, (new_w, new_h))
        except Exception:
            self.logo_image = None

        # ============ POSITIONS ============
        center_x = SCREEN_WIDTH // 2
        btn_width = 300
        btn_height = 60

        if self.logo_image:
            btn_start_y = 80 + self.logo_image.get_height() + 30
        else:
            btn_start_y = 250

        # ============ BOUTONS PRINCIPAUX ============
        self.buttons = [
            Button(
                center_x - btn_width // 2, btn_start_y,
                btn_width, btn_height,
                image_normal=BTN_AVENTURE,
                image_hover=BTN_AVENTURE_HOVER,
                hide_text=True
            ),
            Button(
                center_x - btn_width // 2, btn_start_y + 70,
                btn_width, btn_height,
                image_normal=BTN_PVP,
                image_hover=BTN_PVP_HOVER,
                hide_text=True
            ),
            Button(
                center_x - btn_width // 2, btn_start_y + 140,
                btn_width, btn_height,
                image_normal=BTN_IA,
                image_hover=BTN_IA_HOVER,
                hide_text=True
            ),
        ]

        # ============ BOUTONS DIFFICULTE ============
        diff_btn_width = 200
        diff_btn_height = 50

        self.difficulty_buttons = [
            Button(
                center_x - diff_btn_width // 2, 300,
                diff_btn_width, diff_btn_height,
                image_normal=BTN_FACILE,
                image_hover=BTN_FACILE_HOVER,
                hide_text=True
            ),
            Button(
                center_x - diff_btn_width // 2, 370,
                diff_btn_width, diff_btn_height,
                image_normal=BTN_NORMAL,
                image_hover=BTN_NORMAL_HOVER,
                hide_text=True
            ),
            Button(
                center_x - diff_btn_width // 2, 440,
                diff_btn_width, diff_btn_height,
                image_normal=BTN_DIFFICILE,
                image_hover=BTN_DIFFICILE_HOVER,
                hide_text=True
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
                    elif self.buttons[1].check_click(mouse_pos, True):
                        sound_manager.play_select()
                        self.state_manager.shared_data["mode"] = "pvp"
                        self.state_manager.change_state("selection")
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
        difficulties = ["facile", "normal", "difficile"]
        for i, button in enumerate(self.difficulty_buttons):
            if button.check_click(mouse_pos, True):
                sound_manager.play_select()
                self.state_manager.shared_data["mode"] = "pvia"
                self.state_manager.shared_data["ai_difficulty"] = difficulties[i]
                self.state_manager.change_state("selection")
                return

    def _handle_difficulty_key(self, event):
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
        # Fond
        if self.bg_image:
            surface.blit(self.bg_image, (0, 0))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            surface.blit(overlay, (0, 0))
        else:
            surface.fill(BG_DARK)

        if self._show_difficulty:
            # Logo en petit
            if self.logo_image:
                small_logo = pygame.transform.scale(
                    self.logo_image,
                    (self.logo_image.get_width() // 2, self.logo_image.get_height() // 2)
                )
                logo_x = (SCREEN_WIDTH - small_logo.get_width()) // 2
                surface.blit(small_logo, (logo_x, 20))

            subtitle = self.subtitle_font.render(
                "Choisissez la difficulte", True, WHITE
            )
            sub_x = (SCREEN_WIDTH - subtitle.get_width()) // 2
            surface.blit(subtitle, (sub_x, 260))

            for button in self.difficulty_buttons:
                button.draw(surface)

            hint = self.subtitle_font.render(
                "1 / 2 / 3 ou cliquez | Echap = retour", True, (180, 180, 180)
            )
            hint_x = (SCREEN_WIDTH - hint.get_width()) // 2
            surface.blit(hint, (hint_x, 520))
        else:
            # Logo
            if self.logo_image:
                logo_x = (SCREEN_WIDTH - self.logo_image.get_width()) // 2
                surface.blit(self.logo_image, (logo_x, 80))
            else:
                title = self.title_font.render("POKEMON", True, YELLOW)
                title2 = self.title_font.render("BATTLE ARENA", True, RED)
                surface.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 100))
                surface.blit(title2, ((SCREEN_WIDTH - title2.get_width()) // 2, 160))

            for button in self.buttons:
                button.draw(surface)

            hint = self.subtitle_font.render(
                "ou appuyez sur 1 / 2", True, (180, 180, 180)
            )
            hint_x = (SCREEN_WIDTH - hint.get_width()) // 2
            surface.blit(hint, (hint_x, 500))