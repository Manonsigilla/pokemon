"""Carte Pokemon pour l'ecran de selection - Style Pokedex avec effet flip."""

import pygame
import math

from config import (BLACK, GAME_FONT, WHITE, BORDER_COLOR, TYPE_COLORS,
                    LIGHT_GRAY, BG_LIGHT, YELLOW)


class PokemonCard:
    """Carte cliquable affichant un Pokemon avec effet flip pour les stats."""

    def __init__(self, x, y, width, height, pokemon_id, name, types, sprite, stats=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.pokemon_id = pokemon_id
        self.name = name.capitalize() if name else "???"
        self.types = types or []
        self.sprite = sprite
        self.stats = stats or {}  # {"hp": 100, "attack": 80, ...}
        
        self.is_hovered = False
        self.is_selected = False
        
        # Animation flip
        self.flip_progress = 0.0  # 0 = face avant, 1 = face arrière (stats)
        self.flip_speed = 4.0  # Vitesse de l'animation
        
        # Couleurs style Pokédex
        self.pokedex_red = (220, 50, 50)
        self.pokedex_dark_red = (160, 30, 30)
        self.card_bg = (248, 248, 240)
        self.shadow_color = (30, 30, 30)
        
        self._font_name = None
        self._font_type = None
        self._font_id = None
        self._font_stats = None

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

    @property
    def font_id(self):
        if self._font_id is None:
            self._font_id = pygame.font.Font(None, 16)
        return self._font_id

    @property
    def font_stats(self):
        if self._font_stats is None:
            self._font_stats = pygame.font.Font(None, 15)
        return self._font_stats

    def check_hover(self, mouse_pos):
        """Met a jour l'etat de survol."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def update(self, dt):
        """Met a jour l'animation de flip."""
        target = 1.0 if self.is_hovered else 0.0
        
        if self.flip_progress < target:
            self.flip_progress = min(self.flip_progress + self.flip_speed * dt, target)
        elif self.flip_progress > target:
            self.flip_progress = max(self.flip_progress - self.flip_speed * dt, target)

    def draw(self, surface):
        """Dessine la carte avec effet flip."""
        # Calcul de l'effet de perspective pour le flip
        # flip_progress va de 0 à 1, on le convertit en angle
        angle = self.flip_progress * math.pi  # 0 à PI
        scale_x = abs(math.cos(angle))
        
        # Éviter une largeur nulle
        if scale_x < 0.05:
            scale_x = 0.05
        
        # Rectangle avec effet de scale horizontal (simulation 3D)
        scaled_width = int(self.rect.width * scale_x)
        center_x = self.rect.centerx
        
        draw_rect = pygame.Rect(
            center_x - scaled_width // 2,
            self.rect.y,
            max(scaled_width, 1),
            self.rect.height
        )
        
        # Effet hover - légère élévation
        if self.is_hovered:
            draw_rect.y -= 5
        
        # Ombre portée
        shadow_offset = 6 if self.is_hovered else 3
        shadow_rect = pygame.Rect(
            draw_rect.x + shadow_offset,
            draw_rect.y + shadow_offset,
            draw_rect.width,
            draw_rect.height
        )
        pygame.draw.rect(surface, (40, 40, 40), shadow_rect, border_radius=8)
        
        # Déterminer quelle face afficher
        # Quand cos(angle) > 0, on voit la face avant
        # Quand cos(angle) < 0, on voit la face arrière
        show_back = math.cos(angle) < 0
        
        if show_back:
            self._draw_back(surface, draw_rect)
        else:
            self._draw_front(surface, draw_rect)
        
        # Bordure de sélection
        if self.is_selected:
            pygame.draw.rect(surface, YELLOW, draw_rect, 4, border_radius=8)

    def _draw_front(self, surface, rect):
        """Dessine la face avant de la carte (Pokemon)."""
        # Fond de carte
        pygame.draw.rect(surface, self.card_bg, rect, border_radius=8)
        
        # Bandeau rouge en haut
        header_height = 22
        if rect.width > 20:
            header_rect = pygame.Rect(rect.x, rect.y, rect.width, header_height)
            pygame.draw.rect(surface, self.pokedex_red, header_rect,
                            border_top_left_radius=8, border_top_right_radius=8)
            
            # Numéro du Pokemon
            id_text = self.font_id.render(f"#{self.pokemon_id:03d}", True, WHITE)
            if rect.width > id_text.get_width() + 10:
                surface.blit(id_text, (rect.x + 5, rect.y + 4))
        
        # Zone du sprite
        sprite_zone_y = rect.y + header_height + 2
        sprite_zone_height = rect.height - header_height - 48
        
        if rect.width > 20 and sprite_zone_height > 10:
            sprite_zone = pygame.Rect(rect.x + 6, sprite_zone_y,
                                      rect.width - 12, sprite_zone_height)
            pygame.draw.rect(surface, (235, 235, 225), sprite_zone, border_radius=4)
            
            # Sprite du Pokemon
            if self.sprite and rect.width > 30:
                sprite_rect = self.sprite.get_rect()
                max_size = min(sprite_zone.width - 6, sprite_zone.height - 6)
                
                scale_factor = min(max_size / max(sprite_rect.width, 1),
                                 max_size / max(sprite_rect.height, 1), 1.2)
                
                new_width = max(int(sprite_rect.width * scale_factor), 1)
                new_height = max(int(sprite_rect.height * scale_factor), 1)
                
                scaled_sprite = pygame.transform.scale(self.sprite, (new_width, new_height))
                sprite_x = sprite_zone.centerx - new_width // 2
                sprite_y = sprite_zone.centery - new_height // 2
                surface.blit(scaled_sprite, (sprite_x, sprite_y))
        
        # Nom du Pokemon
        if rect.width > 30:
            name_bg_y = rect.bottom - 44
            name_bg_rect = pygame.Rect(rect.x + 3, name_bg_y, rect.width - 6, 18)
            pygame.draw.rect(surface, (50, 50, 50), name_bg_rect, border_radius=3)
            
            name_text = self.font_name.render(self.name[:12], True, WHITE)
            name_x = name_bg_rect.centerx - name_text.get_width() // 2
            surface.blit(name_text, (name_x, name_bg_y + 2))
        
        # Badges de type
        if rect.width > 40 and self.types:
            badge_y = rect.bottom - 22
            badge_width = min(45, (rect.width - 10) // len(self.types) - 2)
            
            total_width = len(self.types) * badge_width + (len(self.types) - 1) * 3
            badge_x = rect.centerx - total_width // 2
            
            for poke_type in self.types:
                color = TYPE_COLORS.get(poke_type.lower(), LIGHT_GRAY)
                badge_rect = pygame.Rect(badge_x, badge_y, badge_width, 15)
                pygame.draw.rect(surface, color, badge_rect, border_radius=7)
                
                type_text = self.font_type.render(poke_type.upper()[:5], True, WHITE)
                text_x = badge_rect.centerx - type_text.get_width() // 2
                surface.blit(type_text, (text_x, badge_y + 1))
                
                badge_x += badge_width + 3
        
        # Bordure
        pygame.draw.rect(surface, BORDER_COLOR, rect, 2, border_radius=8)

    def _draw_back(self, surface, rect):
        """Dessine la face arrière de la carte (statistiques)."""
        # Fond style Pokédex sombre
        pygame.draw.rect(surface, self.pokedex_dark_red, rect, border_radius=8)
        
        # Header avec nom
        header_height = 24
        if rect.width > 20:
            header_rect = pygame.Rect(rect.x, rect.y, rect.width, header_height)
            pygame.draw.rect(surface, self.pokedex_red, header_rect,
                            border_top_left_radius=8, border_top_right_radius=8)
            
            name_text = self.font_name.render(self.name[:10], True, WHITE)
            name_x = rect.centerx - name_text.get_width() // 2
            surface.blit(name_text, (name_x, rect.y + 4))
        
        # Zone des stats
        if rect.width > 30:
            stats_zone = pygame.Rect(rect.x + 5, rect.y + header_height + 3,
                                     rect.width - 10, rect.height - header_height - 8)
            pygame.draw.rect(surface, (45, 45, 50), stats_zone, border_radius=4)
            
            # Affichage des statistiques
            stat_names = [
                ("hp", "PV"),
                ("attack", "ATK"),
                ("defense", "DEF"),
                ("special-attack", "SPA"),
                ("special-defense", "SPD"),
                ("speed", "VIT")
            ]
            
            y_offset = stats_zone.y + 5
            bar_max_width = stats_zone.width - 45
            
            for stat_key, stat_label in stat_names:
                if stat_key in self.stats and rect.width > 50:
                    value = self.stats[stat_key]
                    
                    # Label
                    label = self.font_stats.render(stat_label, True, WHITE)
                    surface.blit(label, (stats_zone.x + 3, y_offset))
                    
                    # Barre de fond
                    bar_x = stats_zone.x + 32
                    bar_width = bar_max_width
                    bar_height = 8
                    
                    pygame.draw.rect(surface, (70, 70, 70),
                                   (bar_x, y_offset + 3, bar_width, bar_height), border_radius=4)
                    
                    # Barre de valeur (max ~150 pour la plupart des stats)
                    fill_width = int((min(value, 150) / 150) * bar_width)
                    
                    # Couleur selon la valeur
                    if value >= 100:
                        bar_color = (100, 200, 100)  # Vert
                    elif value >= 60:
                        bar_color = (220, 180, 50)  # Jaune/Orange
                    else:
                        bar_color = (200, 80, 80)  # Rouge
                    
                    if fill_width > 0:
                        pygame.draw.rect(surface, bar_color,
                                       (bar_x, y_offset + 3, fill_width, bar_height), border_radius=4)
                    
                    y_offset += 16
        
        # Bordure
        pygame.draw.rect(surface, (100, 100, 100), rect, 2, border_radius=8)