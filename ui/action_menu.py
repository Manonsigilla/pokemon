"""Menu d'action principal en combat : Combat / Pokemon / Fuite."""

import pygame

from config import (BLACK, WHITE, BORDER_COLOR, MENU_BG,
                    DARK_GRAY, LIGHT_GRAY, get_font)


class ActionMenu:
    """Menu avec les actions principales du combat."""

    ACTION_COLORS = {
        "combat": (220, 80, 60),
        "pokemon": (60, 160, 60),
        "fuite": (80, 80, 180),
    }

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.actions = ["combat", "pokemon", "fuite"]
        self.selected_index = 0
        self.visible = False
        self._font = None

    @property
    def font(self):
        if self._font is None:
            self._font = get_font(14)
        return self._font

    def navigate(self, direction):
        """Deplace le curseur parmi les actions."""
        if direction == "up" and self.selected_index > 0:
            self.selected_index -= 1
        elif direction == "down" and self.selected_index < len(self.actions) - 1:
            self.selected_index += 1

    def get_selected_action(self):
        """Retourne l'action selectionnee."""
        return self.actions[self.selected_index]

    def draw(self, surface):
        """Dessine le menu d'actions."""
        if not self.visible:
            return

        # Fond
        pygame.draw.rect(surface, MENU_BG, self.rect)
        pygame.draw.rect(surface, BORDER_COLOR, self.rect, 3)

        btn_height = self.rect.height // len(self.actions)

        labels = {
            "combat": "COMBAT",
            "pokemon": "POKEMON",
            "fuite": "FUITE",
        }

        for i, action in enumerate(self.actions):
            btn_y = self.rect.y + i * btn_height
            btn_rect = pygame.Rect(self.rect.x, btn_y, self.rect.width, btn_height)

            color = self.ACTION_COLORS.get(action, LIGHT_GRAY)
            if i == self.selected_index:
                highlight = tuple(min(255, c + 60) for c in color)
                pygame.draw.rect(surface, highlight, btn_rect)
            else:
                pygame.draw.rect(surface, color, btn_rect)

            pygame.draw.rect(surface, BORDER_COLOR, btn_rect, 1)

            label = labels.get(action, action.upper())
            text_surface = self.font.render(label, True, WHITE)
            text_x = btn_rect.centerx - text_surface.get_width() // 2
            text_y = btn_rect.centery - text_surface.get_height() // 2
            surface.blit(text_surface, (text_x, text_y))

            if i == self.selected_index:
                arrow = self.font.render(">", True, WHITE)
                surface.blit(arrow, (btn_rect.x + 8, text_y))