"""Boite de texte style GBA avec effet machine a ecrire."""

import pygame

from config import BLACK, WHITE, BORDER_COLOR, TEXT_BOX_BG, GAME_FONT


class TextBox:
    """Boite de texte avec animation de frappe caractere par caractere."""

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.full_text = ""
        self.displayed_text = ""
        self.char_index = 0
        self.char_delay = 0.03  # Secondes entre chaque caractere
        self.timer = 0.0
        self.is_complete = False
        self._font = None
        self.padding = 15

    @property
    def font(self):
        if self._font is None:
            self._font = pygame.font.Font(GAME_FONT, 23)
        return self._font

    def set_text(self, text):
        """Definit un nouveau texte et relance l'animation."""
        self.full_text = text
        self.displayed_text = ""
        self.char_index = 0
        self.timer = 0.0
        self.is_complete = False

    def skip_animation(self):
        """Affiche immediatement tout le texte."""
        self.displayed_text = self.full_text
        self.char_index = len(self.full_text)
        self.is_complete = True

    def update(self, dt):
        """Avance l'animation de frappe."""
        if self.is_complete:
            return

        self.timer += dt
        while self.timer >= self.char_delay and self.char_index < len(self.full_text):
            self.timer -= self.char_delay
            self.char_index += 1
            self.displayed_text = self.full_text[:self.char_index]

        if self.char_index >= len(self.full_text):
            self.is_complete = True

    def draw(self, surface):
        """Dessine la boite avec le texte courant."""
        # Fond
        pygame.draw.rect(surface, TEXT_BOX_BG, self.rect)
        # Bordure
        pygame.draw.rect(surface, BORDER_COLOR, self.rect, 3)

        # Texte avec retour a la ligne
        if self.displayed_text:
            self._draw_wrapped_text(surface, self.displayed_text)

        # Indicateur "suite" (triangle)
        if self.is_complete and self.full_text:
            triangle_x = self.rect.right - 25
            triangle_y = self.rect.bottom - 20
            points = [
                (triangle_x, triangle_y),
                (triangle_x + 10, triangle_y),
                (triangle_x + 5, triangle_y + 8),
            ]
            pygame.draw.polygon(surface, BLACK, points)

    def _draw_wrapped_text(self, surface, text):
        """Dessine le texte avec retour a la ligne automatique."""
        max_width = self.rect.width - self.padding * 2
        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_width = self.font.size(test_line)[0]
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        y = self.rect.y + self.padding
        for line in lines[:4]:  # Max 4 lignes
            text_surface = self.font.render(line, True, BLACK)
            surface.blit(text_surface, (self.rect.x + self.padding, y))
            y += 30
