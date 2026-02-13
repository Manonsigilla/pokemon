"""Numéros de dégâts flottants animés."""

import pygame


class DamageNumber:
    """Affiche un nombre de dégâts qui flotte et disparaît."""
    
    def __init__(self, damage, position, is_critical=False, is_effective=None):
        self.damage = damage
        self.position = list(position)
        self.original_y = position[1]
        self.is_critical = is_critical
        self.is_effective = is_effective
        
        self.duration = 1.5
        self.elapsed = 0.0
        self.is_complete = False
        
        # Vitesse de montée
        self.rise_speed = -80  # Pixels par seconde
        
        # Font
        size = 48 if is_critical else 36
        self._font = pygame.font.Font(None, size)
        
        # Couleur selon efficacité
        if is_effective is None or is_effective == 1.0:
            self.color = (255, 255, 255)
        elif is_effective >= 2.0:
            self.color = (100, 255, 100)  # Vert
        elif is_effective > 1.0:
            self.color = (200, 255, 150)
        elif is_effective == 0:
            self.color = (150, 150, 150)  # Gris
        else:
            self.color = (255, 150, 150)  # Rouge clair
    
    def update(self, dt):
        """Met à jour l'animation."""
        self.elapsed += dt
        
        if self.elapsed >= self.duration:
            self.is_complete = True
            return
        
        # Monte progressivement
        self.position[1] += self.rise_speed * dt
    
    def draw(self, surface):
        """Dessine le nombre de dégâts."""
        if self.is_complete:
            return
        
        # Alpha fade out
        progress = self.elapsed / self.duration
        alpha = int(255 * (1 - progress))
        
        # Texte
        text = f"-{self.damage}"
        if self.is_critical:
            text += "!"
        
        # Rendu avec ombre
        shadow = self._font.render(text, True, (0, 0, 0))
        shadow.set_alpha(alpha)
        
        color_with_alpha = self.color
        text_surface = self._font.render(text, True, color_with_alpha)
        text_surface.set_alpha(alpha)
        
        # Position centrée
        x = int(self.position[0] - text_surface.get_width() // 2)
        y = int(self.position[1])
        
        # Dessiner ombre puis texte
        surface.blit(shadow, (x + 2, y + 2))
        surface.blit(text_surface, (x, y))