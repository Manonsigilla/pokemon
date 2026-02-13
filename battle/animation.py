"""Système d'animation pour les combats Pokemon."""

import pygame
import random
import math


class AttackAnimation:
    """Animation complète d'une attaque : mouvement + impact."""
    
    def __init__(self, attacker_pos, defender_pos, is_player):
        self.attacker_pos = list(attacker_pos)
        self.defender_pos = defender_pos
        self.original_pos = attacker_pos[:]
        self.is_player = is_player
        
        # Phases : move_forward -> impact -> move_back
        self.phase = "move_forward"
        self.progress = 0.0
        self.speed = 3.0
        self.is_complete = False
        
        # Calcul de la direction
        dx = defender_pos[0] - attacker_pos[0]
        dy = defender_pos[1] - attacker_pos[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            self.direction = (dx / distance, dy / distance)
        else:
            self.direction = (1, 0)
        
        self.attack_distance = 80
    
    def update(self, dt):
        """Met à jour l'animation."""
        if self.is_complete:
            return
        
        self.progress += self.speed * dt
        
        if self.phase == "move_forward":
            if self.progress >= 1.0:
                self.progress = 0.0
                self.phase = "impact"
            else:
                t = self._ease_out_quad(self.progress)
                self.attacker_pos[0] = self.original_pos[0] + self.direction[0] * self.attack_distance * t
                self.attacker_pos[1] = self.original_pos[1] + self.direction[1] * self.attack_distance * t
        
        elif self.phase == "impact":
            if self.progress >= 0.3:
                self.progress = 0.0
                self.phase = "move_back"
        
        elif self.phase == "move_back":
            if self.progress >= 1.0:
                self.attacker_pos[0] = self.original_pos[0]
                self.attacker_pos[1] = self.original_pos[1]
                self.is_complete = True
            else:
                t = self._ease_in_quad(1.0 - self.progress)
                self.attacker_pos[0] = self.original_pos[0] + self.direction[0] * self.attack_distance * t
                self.attacker_pos[1] = self.original_pos[1] + self.direction[1] * self.attack_distance * t
    
    def _ease_out_quad(self, t):
        return 1 - (1 - t) * (1 - t)
    
    def _ease_in_quad(self, t):
        return t * t
    
    def get_attacker_position(self):
        return tuple(self.attacker_pos)
    
    def should_show_impact(self):
        return self.phase == "impact"


class ShakeAnimation:
    """Animation de secousse pour le Pokemon qui prend des dégâts."""
    
    def __init__(self, original_pos, intensity=10):
        self.original_pos = original_pos
        self.current_pos = list(original_pos)
        self.intensity = intensity
        self.duration = 0.4
        self.elapsed = 0.0
        self.is_complete = False
    
    def update(self, dt):
        if self.is_complete:
            return
        
        self.elapsed += dt
        
        if self.elapsed >= self.duration:
            self.current_pos = list(self.original_pos)
            self.is_complete = True
        else:
            progress = self.elapsed / self.duration
            current_intensity = self.intensity * (1 - progress)
            
            offset_x = random.randint(-int(current_intensity), int(current_intensity))
            offset_y = random.randint(-int(current_intensity), int(current_intensity))
            
            self.current_pos[0] = self.original_pos[0] + offset_x
            self.current_pos[1] = self.original_pos[1] + offset_y
    
    def get_position(self):
        return tuple(self.current_pos)


class ImpactParticles:
    """Particules d'impact lors d'une attaque."""
    
    def __init__(self, position, color=(255, 255, 100)):
        self.particles = []
        self.position = position
        self.is_complete = False
        
        # Valider la couleur
        if isinstance(color, (list, tuple)) and len(color) >= 3:
            validated_color = (
                int(max(0, min(255, color[0]))),
                int(max(0, min(255, color[1]))),
                int(max(0, min(255, color[2])))
            )
        else:
            validated_color = (255, 255, 100)
        
        # Créer les particules
        num_particles = random.randint(15, 20)
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 250)
            
            self.particles.append({
                'x': position[0],
                'y': position[1],
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(0.3, 0.6),
                'max_life': random.uniform(0.3, 0.6),
                'size': random.randint(3, 7),
                'color': validated_color
            })
    
    def update(self, dt):
        active_particles = 0
        
        for particle in self.particles:
            particle['life'] -= dt
            
            if particle['life'] > 0:
                active_particles += 1
                particle['x'] += particle['vx'] * dt
                particle['y'] += particle['vy'] * dt
                particle['vy'] += 400 * dt
        
        if active_particles == 0:
            self.is_complete = True
    
    def draw(self, surface):
        for particle in self.particles:
            if particle['life'] > 0:
                try:
                    alpha = int(255 * (particle['life'] / particle['max_life']))
                    size = int(particle['size'] * (particle['life'] / particle['max_life']))
                    
                    if size > 0:
                        s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                        
                        base_color = particle['color']
                        r = max(0, min(255, int(base_color[0])))
                        g = max(0, min(255, int(base_color[1])))
                        b = max(0, min(255, int(base_color[2])))
                        a = max(0, min(255, int(alpha)))
                        color = (r, g, b, a)
                        
                        pygame.draw.circle(s, color, (size, size), size)
                        surface.blit(s, (int(particle['x']) - size, int(particle['y']) - size))
                except:
                    continue


class EffectivenessFlash:
    """Flash coloré selon l'efficacité de l'attaque."""
    
    def __init__(self, effectiveness):
        self.effectiveness = effectiveness
        self.duration = 0.3
        self.elapsed = 0.0
        self.is_complete = False
        
        if effectiveness >= 2.0:
            self.color = (100, 255, 100)
        elif effectiveness > 1.0:
            self.color = (150, 255, 150)
        elif effectiveness == 0:
            self.color = (100, 100, 100)
        elif effectiveness < 1.0:
            self.color = (255, 100, 100)
        else:
            self.color = (255, 255, 255)
    
    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.is_complete = True
    
    def get_alpha(self):
        if self.is_complete:
            return 0
        
        progress = self.elapsed / self.duration
        if progress < 0.5:
            return int(120 * (progress / 0.5))
        else:
            return int(120 * (1 - (progress - 0.5) / 0.5))
    
    def draw(self, surface):
        alpha = self.get_alpha()
        if alpha > 0:
            flash = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
            flash.fill(self.color + (alpha,))
            surface.blit(flash, (0, 0))