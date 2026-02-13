"""Widget bouton cliquable."""

import pygame

from config import BLACK, WHITE, DARK_GRAY, LIGHT_GRAY, BORDER_COLOR


class Button:
    """Bouton cliquable avec texte centre."""

    def __init__(self, x, y, width, height, text, font=None, font_size=24):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_hovered = False
        self.font_size = font_size
        self._font = font

    @property
    def font(self):
        if self._font is None:
            self._font = pygame.font.Font(None, self.font_size)
        return self._font

    def check_hover(self, mouse_pos):
        """Met a jour l'etat de survol."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def check_click(self, mouse_pos, mouse_pressed):
        """Retourne True si le bouton est clique."""
        return self.rect.collidepoint(mouse_pos) and mouse_pressed

    def draw(self, surface):
        """Dessine le bouton."""
        # Fond
        bg_color = LIGHT_GRAY if self.is_hovered else WHITE
        pygame.draw.rect(surface, bg_color, self.rect)

        # Bordure
        pygame.draw.rect(surface, BORDER_COLOR, self.rect, 3)

        # Texte centre
        text_surface = self.font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
