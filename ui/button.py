"""Widget bouton cliquable avec support d'images."""

import pygame

from config import BLACK, WHITE, DARK_GRAY, LIGHT_GRAY, BORDER_COLOR, get_font


class Button:
    """Bouton cliquable avec image de fond ou texte simple."""

    def __init__(self, x, y, width, height, text, font=None, font_size=14, image_normal=None, image_hover=None):
        """
        Args:
            x, y, width, height: Position et taille du bouton
            text: Texte a afficher sur le bouton
            image_normal: Chemin vers l'image du bouton (etat normal)
            image_hover: Chemin vers l'image du bouton (etat survol)
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_hovered = False
        self.font_size = font_size
        self._font = font

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
        """Met a jour l'etat de survol."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def check_click(self, mouse_pos, mouse_pressed):
        """Retourne True si le bouton est clique."""
        return self.rect.collidepoint(mouse_pos) and mouse_pressed

    def draw(self, surface):
        """Dessine le bouton avec image ou fallback texte."""
        if self.img_normal:
            # Mode image
            if self.is_hovered and self.img_hover:
                surface.blit(self.img_hover, self.rect.topleft)
            else:
                surface.blit(self.img_normal, self.rect.topleft)

            # Texte par dessus l'image
            text_surface = self.font.render(self.text, True, WHITE)
            text_rect = text_surface.get_rect(center=self.rect.center)
            surface.blit(text_surface, text_rect)
        else:
            # Fallback : bouton classique sans image
            bg_color = LIGHT_GRAY if self.is_hovered else WHITE
            pygame.draw.rect(surface, bg_color, self.rect)
            pygame.draw.rect(surface, BORDER_COLOR, self.rect, 3)

            text_surface = self.font.render(self.text, True, BLACK)
            text_rect = text_surface.get_rect(center=self.rect.center)
            surface.blit(text_surface, text_rect)