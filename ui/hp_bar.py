"""Widget barre de vie animee style GBA."""

import pygame

from pokemon.config import (BLACK, WHITE, HP_GREEN, HP_YELLOW, HP_RED,
                    BORDER_COLOR, BG_LIGHT)


class HPBar:
    """Barre de vie animee avec nom du Pokemon et niveau."""

    def __init__(self, x, y, width, pokemon, show_hp_text=True):
        self.x = x
        self.y = y
        self.width = width
        self.bar_height = 8
        self.pokemon = pokemon
        self.show_hp_text = show_hp_text

        # Animation douce
        self.displayed_hp = float(pokemon.current_hp)
        self.animation_speed = 150  # PV par seconde

        self._font_name = None
        self._font_hp = None

    @property
    def font_name(self):
        if self._font_name is None:
            self._font_name = pygame.font.Font(None, 28)
        return self._font_name

    @property
    def font_hp(self):
        if self._font_hp is None:
            self._font_hp = pygame.font.Font(None, 22)
        return self._font_hp

    def update(self, dt):
        """Anime la barre vers la valeur reelle des PV."""
        target = float(self.pokemon.current_hp)
        if self.displayed_hp > target:
            self.displayed_hp = max(target, self.displayed_hp - self.animation_speed * dt)
        elif self.displayed_hp < target:
            self.displayed_hp = min(target, self.displayed_hp + self.animation_speed * dt)

    @property
    def is_animating(self):
        """True si la barre est encore en animation."""
        return abs(self.displayed_hp - self.pokemon.current_hp) > 0.5

    def draw(self, surface):
        """Dessine le panneau d'info complet : nom, niveau, barre, texte PV."""
        # Fond du panneau
        panel_width = self.width + 20
        panel_height = 65 if self.show_hp_text else 50
        panel_rect = pygame.Rect(self.x - 10, self.y - 5, panel_width, panel_height)
        pygame.draw.rect(surface, BG_LIGHT, panel_rect)
        pygame.draw.rect(surface, BORDER_COLOR, panel_rect, 2)

        # Nom et niveau
        name_text = self.font_name.render(
            f"{self.pokemon.name}", True, BLACK
        )
        level_text = self.font_name.render(
            f"Nv.{self.pokemon.level}", True, BLACK
        )
        surface.blit(name_text, (self.x, self.y))
        level_x = self.x + self.width - level_text.get_width()
        surface.blit(level_text, (level_x, self.y))

        # Barre de vie
        bar_y = self.y + 25
        bar_rect = pygame.Rect(self.x, bar_y, self.width, self.bar_height)

        # Fond de la barre (gris)
        pygame.draw.rect(surface, BLACK, bar_rect)

        # Remplissage
        if self.pokemon.max_hp > 0:
            fill_ratio = max(0, self.displayed_hp / self.pokemon.max_hp)
        else:
            fill_ratio = 0
        fill_width = int(self.width * fill_ratio)

        if fill_width > 0:
            fill_color = self._get_bar_color(fill_ratio)
            fill_rect = pygame.Rect(self.x, bar_y, fill_width, self.bar_height)
            pygame.draw.rect(surface, fill_color, fill_rect)

        # Bordure de la barre
        pygame.draw.rect(surface, BORDER_COLOR, bar_rect, 1)

        # Texte PV
        if self.show_hp_text:
            hp_text = self.font_hp.render(
                f"{max(0, int(self.displayed_hp))}/{self.pokemon.max_hp}",
                True, BLACK
            )
            hp_x = self.x + self.width - hp_text.get_width()
            surface.blit(hp_text, (hp_x, bar_y + 12))

        # Indicateur de statut
        if self.pokemon.status:
            status_text = self.font_hp.render(
                str(self.pokemon.status), True, (200, 50, 50)
            )
            surface.blit(status_text, (self.x, bar_y + 12))

    def _get_bar_color(self, ratio):
        """Vert > 50%, Jaune > 20%, Rouge sinon."""
        if ratio > 0.5:
            return HP_GREEN
        elif ratio > 0.2:
            return HP_YELLOW
        return HP_RED
