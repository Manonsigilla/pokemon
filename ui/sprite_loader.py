"""Chargement et mise a l'echelle des sprites Pokemon."""

import pygame

from config import SPRITE_SCALE


class SpriteLoader:
    """Charge et met a l'echelle les sprites pour Pygame."""

    def __init__(self):
        self.cache = {}

    def load_sprite(self, file_path, scale=SPRITE_SCALE):
        """Charge un sprite, le scale en nearest-neighbor pour un look pixel art."""
        cache_key = f"{file_path}_{scale}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        sprite = pygame.image.load(file_path).convert_alpha()
        width = sprite.get_width() * scale
        height = sprite.get_height() * scale
        sprite = pygame.transform.scale(sprite, (width, height))

        self.cache[cache_key] = sprite
        return sprite

    def load_sprite_small(self, file_path, scale=2):
        """Charge un sprite avec un scale plus petit (pour l'ecran de selection)."""
        return self.load_sprite(file_path, scale)
