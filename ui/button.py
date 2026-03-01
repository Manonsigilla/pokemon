"""Widget bouton cliquable avec support d'images."""

import pygame

from config import BLACK, WHITE, DARK_GRAY, LIGHT_GRAY, BORDER_COLOR, get_font


class Button:
    """Bouton cliquable avec image de fond ou texte simple."""

    def __init__(self, x, y, width, height, text="", font=None, font_size=14, image_normal=None, image_hover=None, hide_text=False, color=None, hover_color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_hovered = False
        self.font_size = font_size
        self._font = font
        self.hide_text = hide_text  # True = pas de texte (deja dans l'image)
        self.color = color
        self.hover_color = hover_color

        # Images du bouton
        self.img_normal = None
        self.img_hover = None

        if image_normal:
            try:
                img = pygame.image.load(image_normal).convert_alpha()
                self.img_normal = pygame.transform.scale(img, (width, height))
            except Exception as e:
                print(f"[Button] Erreur chargement image normal: {e}")

        if image_hover:
            try:
                img = pygame.image.load(image_hover).convert_alpha()
                self.img_hover = pygame.transform.scale(img, (width, height))
            except Exception as e:
                print(f"[Button] Erreur chargement image hover: {e}")

    @property
    def font(self):
        if self._font is None:
            self._font = get_font(self.font_size)
        return self._font

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def check_click(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed

    def draw(self, surface):
        if self.img_normal:
            # Mode image
            if self.is_hovered and self.img_hover:
                surface.blit(self.img_hover, self.rect.topleft)
            else:
                surface.blit(self.img_normal, self.rect.topleft)

            # Texte par dessus seulement si hide_text est False
            if not self.hide_text and self.text:
                text_surface = self.font.render(self.text, True, WHITE)
                text_rect = text_surface.get_rect(center=self.rect.center)
                surface.blit(text_surface, text_rect)
        else:
            # Fallback classique (avec couleur custom si fournie)
            if self.color:
                bg_color = self.hover_color if (self.is_hovered and self.hover_color) else self.color
                pygame.draw.rect(surface, bg_color, self.rect, border_radius=8)
                pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=8)
                text_color = WHITE
            else:
                bg_color = LIGHT_GRAY if self.is_hovered else WHITE
                pygame.draw.rect(surface, bg_color, self.rect)
                pygame.draw.rect(surface, BORDER_COLOR, self.rect, 3)
                text_color = BLACK

            if self.text:
                text_surface = self.font.render(self.text, True, text_color)
                text_rect = text_surface.get_rect(center=self.rect.center)
                surface.blit(text_surface, text_rect)