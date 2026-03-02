"""Chargement et mise a l'echelle des sprites Pokemon."""

import pygame

from config import SPRITE_SCALE


class SpriteLoader:
    """Charge et met a l'echelle les sprites pour Pygame."""

    def __init__(self):
        self.cache = {}

    def load_sprite(self, file_path, scale=SPRITE_SCALE):
        """Charge un sprite, le scale en nearest-neighbor pour un look pixel art."""
        
        if not file_path:
            # Retourner une surface vide plutôt que de planter
            placeholder = pygame.Surface((96, 96), pygame.SRCALPHA)
            placeholder.fill((200, 50, 200, 180))  # Violet = sprite manquant visible
            return placeholder
        
        cache_key = f"{file_path}_{scale}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            sprite = pygame.image.load(file_path).convert_alpha()
        except Exception as e:
            print(f"[SpriteLoader] Impossible de charger '{file_path}': {e}")
            placeholder = pygame.Surface((96, 96), pygame.SRCALPHA)
            placeholder.fill((200, 50, 200, 180))
            return placeholder
        
        width = sprite.get_width() * scale
        height = sprite.get_height() * scale
        sprite = pygame.transform.scale(sprite, (width, height))

        self.cache[cache_key] = sprite
        return sprite

    def load_sprite_small(self, file_path, scale=2):
        """Charge un sprite avec un scale plus petit (pour l'ecran de selection)."""
        return self.load_sprite(file_path, scale)
