"""Carte Pokemon pour l'ecran de selection."""

import pygame

from config import (BLACK, WHITE, BORDER_COLOR, TYPE_COLORS,
                    LIGHT_GRAY, BG_LIGHT)
from config import GAME_FONT

class PokemonCard:
    """Carte cliquable affichant un Pokemon pour la selection."""

    def __init__(self, x, y, width, height, pokemon_id, name, types, sprite):
        self.rect = pygame.Rect(x, y, width, height)
        self.pokemon_id = pokemon_id
        self.name = name
        self.types = types
        self.sprite = sprite
        self.is_hovered = False
        self.is_selected = False
        self._font_name = None
        self._font_type = None

    @property
    def font_name(self):
        if self._font_name is None:
            self._font_name = pygame.font.Font(GAME_FONT, 18)
        return self._font_name

    @property
    def font_type(self):
        if self._font_type is None:
            self._font_type = pygame.font.Font(GAME_FONT, 13)
        return self._font_type

    def check_hover(self, mouse_pos):
        """Met a jour l'etat de survol."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def draw(self, surface):
        """Dessine la carte avec sprite, nom et badges de type."""
        # Fond
        if self.is_selected:
            bg_color = (180, 230, 180)
        elif self.is_hovered:
            bg_color = (230, 230, 250)
        else:
            bg_color = BG_LIGHT

        pygame.draw.rect(surface, bg_color, self.rect)

        # Bordure
        border_color = (50, 180, 50) if self.is_selected else BORDER_COLOR
        border_width = 3 if self.is_selected or self.is_hovered else 2
        pygame.draw.rect(surface, border_color, self.rect, border_width)

        # Sprite centre en haut
        if self.sprite:
            sprite_x = self.rect.x + (self.rect.width - self.sprite.get_width()) // 2
            sprite_y = self.rect.y + 5
            surface.blit(self.sprite, (sprite_x, sprite_y))

        # Nom
        name_surface = self.font_name.render(self.name, True, BLACK)
        name_x = self.rect.x + (self.rect.width - name_surface.get_width()) // 2
        name_y = self.rect.bottom - 40
        surface.blit(name_surface, (name_x, name_y))

        # Badges de type
        badge_y = self.rect.bottom - 20
        total_width = len(self.types) * 55 + (len(self.types) - 1) * 5
        badge_x = self.rect.x + (self.rect.width - total_width) // 2

        for poke_type in self.types:
            color = TYPE_COLORS.get(poke_type, LIGHT_GRAY)
            badge_rect = pygame.Rect(badge_x, badge_y, 55, 16)
            pygame.draw.rect(surface, color, badge_rect, border_radius=3)
            pygame.draw.rect(surface, BLACK, badge_rect, 1, border_radius=3)

            type_text = self.font_type.render(poke_type.title(), True, WHITE)
            text_x = badge_x + (55 - type_text.get_width()) // 2
            surface.blit(type_text, (text_x, badge_y + 1))

            badge_x += 60
