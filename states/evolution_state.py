"""Ecran d'animation d'evolution Pokemon."""

import math
import pygame

from states.state import State
from ui.sprite_loader import SpriteLoader
from ui.sound_manager import sound_manager
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW,
                    BG_DARK, get_font, render_fitted_text)


class EvolutionState(State):
    """Animation d'evolution : ancien sprite -> flash -> nouveau sprite."""

    # Phases de l'animation
    PHASE_INTRO = "intro"              # "Quoi? [nom] evolue !"
    PHASE_FLASH_LOOP = "flash_loop"    # Clignotement ancien/nouveau de plus en plus rapide
    PHASE_WHITE_FLASH = "white_flash"  # Grand flash blanc
    PHASE_REVEAL = "reveal"            # Nouveau sprite apparait
    PHASE_MESSAGE = "message"          # "[ancien] evolue en [nouveau] !"
    PHASE_DONE = "done"                # Attente Entree puis prochain ou fin

    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.sprite_loader = SpriteLoader()

        # Donnees d'evolution
        self.evolutions_queue = []   # Liste de (pokemon, evo_data, api)
        self.current_index = 0

        # Sprites
        self.old_sprite = None
        self.new_sprite = None
        self.old_name = ""
        self.new_name = ""

        # Animation
        self.phase = self.PHASE_INTRO
        self.timer = 0.0
        self.flash_alpha = 0
        self.flash_cycle = 0.0
        self.flash_speed = 3.0       # Vitesse initiale du clignotement
        self.show_new = False         # Alterner ancien/nouveau pendant le flash
        self.reveal_alpha = 0        # Alpha du nouveau sprite pendant le reveal
        self.particle_list = []       # Particules d'etincelles
        self.pulse_timer = 0.0        # Pulsation du sprite

        # Fonts
        self._font_title = None
        self._font_msg = None
        self._font_hint = None

    @property
    def font_title(self):
        if self._font_title is None:
            self._font_title = get_font(24)
        return self._font_title

    @property
    def font_msg(self):
        if self._font_msg is None:
            self._font_msg = get_font(20)
        return self._font_msg

    @property
    def font_hint(self):
        if self._font_hint is None:
            self._font_hint = get_font(14)
        return self._font_hint

    def enter(self):
        """Recupere la liste des evolutions a jouer."""
        self.evolutions_queue = self.state_manager.shared_data.pop("evolutions_to_play", [])
        self.current_index = 0

        if self.evolutions_queue:
            self._start_current_evolution()
        else:
            # Rien a evoluer, passer directement au resultat
            self._go_to_result()

    def _start_current_evolution(self):
        """Demarre l'animation pour l'evolution courante."""
        pokemon, evo_data, api = self.evolutions_queue[self.current_index]

        self.old_name = pokemon.name
        self.evo_data = evo_data
        self.pokemon = pokemon
        self.api = api

        # Charger l'ancien sprite
        try:
            self.old_sprite = self.sprite_loader.load_sprite(
                pokemon.front_sprite_path, scale=4
            )
        except Exception:
            self.old_sprite = None

        # Telecharger et charger le nouveau sprite
        try:
            new_front = api.download_sprite(evo_data["id"], "front")
            self.new_sprite = self.sprite_loader.load_sprite(new_front, scale=4)
        except Exception:
            self.new_sprite = None

        self.new_name = evo_data["name"].title()

        # Reset animation
        self.phase = self.PHASE_INTRO
        self.timer = 0.0
        self.flash_alpha = 0
        self.flash_cycle = 0.0
        self.flash_speed = 3.0
        self.show_new = False
        self.reveal_alpha = 0
        self.particle_list = []
        self.pulse_timer = 0.0

        # Musique d'evolution (si dispo, sinon on garde le silence)
        sound_manager.stop_music()

    def _apply_evolution(self):
        """Applique reellement l'evolution sur l'objet Pokemon."""
        pokemon = self.pokemon
        evo_data = self.evo_data
        api = self.api

        try:
            front_sprite = api.download_sprite(evo_data["id"], "front")
            back_sprite = api.download_sprite(evo_data["id"], "back")

            pokemon.evolve(
                new_id=evo_data["id"],
                new_name=evo_data["name"],
                new_types=evo_data["types"],
                new_base_stats=evo_data["stats"],
                new_front_sprite=front_sprite,
                new_back_sprite=back_sprite,
            )
        except Exception as e:
            print(f"[EvolutionState] Erreur application evolution: {e}")

    def _go_to_result(self):
        """Passe a l'ecran de resultat."""
        self.state_manager.change_state("result")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.phase == self.PHASE_INTRO:
                    # Appuyer pour lancer l'animation
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.phase = self.PHASE_FLASH_LOOP
                        self.timer = 0.0

                elif self.phase == self.PHASE_DONE:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        # Prochain pokemon ou fin
                        self.current_index += 1
                        if self.current_index < len(self.evolutions_queue):
                            self._start_current_evolution()
                        else:
                            self._go_to_result()

    def update(self, dt):
        self.timer += dt
        self.pulse_timer += dt

        if self.phase == self.PHASE_FLASH_LOOP:
            # Clignotement de plus en plus rapide pendant 3 secondes
            self.flash_cycle += self.flash_speed * dt
            self.flash_speed += dt * 4.0  # Accelere progressivement

            # Alterner ancien/nouveau
            self.show_new = math.sin(self.flash_cycle) > 0

            # Flash blanc de fond qui s'intensifie
            progress = min(self.timer / 3.0, 1.0)
            self.flash_alpha = int(progress * 200)

            # Generer des particules
            if self.timer > 1.0 and len(self.particle_list) < 60:
                import random
                cx = SCREEN_WIDTH // 2
                cy = SCREEN_HEIGHT // 2
                for _ in range(2):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(60, 180)
                    self.particle_list.append({
                        "x": cx + random.randint(-40, 40),
                        "y": cy + random.randint(-40, 40),
                        "vx": math.cos(angle) * speed,
                        "vy": math.sin(angle) * speed - 50,
                        "life": random.uniform(0.5, 1.2),
                        "max_life": random.uniform(0.5, 1.2),
                        "size": random.randint(3, 6),
                    })

            if self.timer >= 3.0:
                self.phase = self.PHASE_WHITE_FLASH
                self.timer = 0.0
                self.flash_alpha = 255
                self._apply_evolution()
                sound_manager.play_sfx("super_effective")

        elif self.phase == self.PHASE_WHITE_FLASH:
            # Flash blanc total pendant 0.6s puis fadeout
            if self.timer < 0.3:
                self.flash_alpha = 255
            else:
                fade_progress = (self.timer - 0.3) / 0.5
                self.flash_alpha = int(255 * max(0, 1.0 - fade_progress))

            if self.timer >= 0.8:
                self.phase = self.PHASE_REVEAL
                self.timer = 0.0
                self.reveal_alpha = 0

        elif self.phase == self.PHASE_REVEAL:
            # Nouveau sprite apparait en fondu
            self.reveal_alpha = min(255, int(self.timer / 0.8 * 255))

            if self.timer >= 1.2:
                self.phase = self.PHASE_MESSAGE
                self.timer = 0.0

        elif self.phase == self.PHASE_MESSAGE:
            # Affiche le message pendant 2s puis passe a DONE
            if self.timer >= 2.0:
                self.phase = self.PHASE_DONE

        # Mettre a jour les particules
        for p in self.particle_list[:]:
            p["life"] -= dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 100 * dt  # gravite legere
            if p["life"] <= 0:
                self.particle_list.remove(p)

    def draw(self, surface):
        surface.fill(BG_DARK)

        # Position centrale du sprite
        sprite_cx = SCREEN_WIDTH // 2
        sprite_cy = SCREEN_HEIGHT // 2 - 20

        # ============ PHASE INTRO ============
        if self.phase == self.PHASE_INTRO:
            # Ancien sprite au centre
            if self.old_sprite:
                sx = sprite_cx - self.old_sprite.get_width() // 2
                sy = sprite_cy - self.old_sprite.get_height() // 2
                surface.blit(self.old_sprite, (sx, sy))

            # Texte "Quoi? [nom] evolue !"
            text_str = f"Quoi ? {self.old_name} evolue !"
            text = render_fitted_text(text_str, SCREEN_WIDTH - 40, 24, WHITE, min_size=14)
            tx = (SCREEN_WIDTH - text.get_width()) // 2
            surface.blit(text, (tx, SCREEN_HEIGHT - 120))

            hint = self.font_hint.render("Appuyez sur Entree...", True, (150, 150, 150))
            surface.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, SCREEN_HEIGHT - 70))

        # ============ PHASE FLASH LOOP ============
        elif self.phase == self.PHASE_FLASH_LOOP:
            # Pulsation du sprite
            pulse = 1.0 + 0.05 * math.sin(self.pulse_timer * 8)

            sprite_to_show = self.new_sprite if self.show_new else self.old_sprite
            if sprite_to_show:
                w = int(sprite_to_show.get_width() * pulse)
                h = int(sprite_to_show.get_height() * pulse)
                scaled = pygame.transform.scale(sprite_to_show, (w, h))

                # Teinte blanche qui s'intensifie
                progress = min(self.timer / 3.0, 1.0)
                white_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
                white_overlay.fill((255, 255, 255, int(progress * 180)))

                sx = sprite_cx - w // 2
                sy = sprite_cy - h // 2
                surface.blit(scaled, (sx, sy))
                surface.blit(white_overlay, (sx, sy))

            # Particules
            self._draw_particles(surface)

            # Texte
            text = render_fitted_text(
                f"{self.old_name} evolue...", SCREEN_WIDTH - 40, 22, YELLOW, min_size=12
            )
            surface.blit(text, ((SCREEN_WIDTH - text.get_width()) // 2, SCREEN_HEIGHT - 100))

        # ============ PHASE WHITE FLASH ============
        elif self.phase == self.PHASE_WHITE_FLASH:
            # Nouveau sprite commence a apparaitre derriere le flash
            if self.new_sprite and self.timer > 0.3:
                sx = sprite_cx - self.new_sprite.get_width() // 2
                sy = sprite_cy - self.new_sprite.get_height() // 2
                surface.blit(self.new_sprite, (sx, sy))

        # ============ PHASE REVEAL ============
        elif self.phase == self.PHASE_REVEAL:
            if self.new_sprite:
                # Effet de scale-in
                progress = min(self.timer / 0.8, 1.0)
                scale = 0.5 + 0.5 * self._ease_out_back(progress)
                w = int(self.new_sprite.get_width() * scale)
                h = int(self.new_sprite.get_height() * scale)

                if w > 0 and h > 0:
                    scaled = pygame.transform.scale(self.new_sprite, (w, h))
                    scaled.set_alpha(self.reveal_alpha)
                    sx = sprite_cx - w // 2
                    sy = sprite_cy - h // 2
                    surface.blit(scaled, (sx, sy))

            # Particules dorées de celebration
            self._draw_particles(surface)

            # Generer des etincelles dorees
            if len(self.particle_list) < 30:
                import random
                for _ in range(3):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(40, 120)
                    self.particle_list.append({
                        "x": sprite_cx + random.randint(-60, 60),
                        "y": sprite_cy + random.randint(-60, 60),
                        "vx": math.cos(angle) * speed,
                        "vy": math.sin(angle) * speed - 80,
                        "life": random.uniform(0.4, 1.0),
                        "max_life": random.uniform(0.4, 1.0),
                        "size": random.randint(2, 5),
                    })

        # ============ PHASE MESSAGE ============
        elif self.phase in (self.PHASE_MESSAGE, self.PHASE_DONE):
            # Nouveau sprite avec legere pulsation
            if self.new_sprite:
                pulse = 1.0 + 0.02 * math.sin(self.pulse_timer * 3)
                w = int(self.new_sprite.get_width() * pulse)
                h = int(self.new_sprite.get_height() * pulse)
                scaled = pygame.transform.scale(self.new_sprite, (w, h))
                sx = sprite_cx - w // 2
                sy = sprite_cy - h // 2
                surface.blit(scaled, (sx, sy))

            # Particules restantes
            self._draw_particles(surface)

            # Message d'evolution en dore
            msg_str = f"{self.old_name} a evolue en {self.new_name} !"
            msg_text = render_fitted_text(msg_str, SCREEN_WIDTH - 40, 22, (255, 223, 100), min_size=14)
            surface.blit(msg_text, ((SCREEN_WIDTH - msg_text.get_width()) // 2, SCREEN_HEIGHT - 110))

            if self.phase == self.PHASE_DONE:
                hint = self.font_hint.render("Appuyez sur Entree...", True, (180, 180, 180))
                surface.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, SCREEN_HEIGHT - 60))

        # ============ FLASH BLANC PAR DESSUS ============
        if self.flash_alpha > 0:
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surface.fill(WHITE)
            flash_surface.set_alpha(min(255, self.flash_alpha))
            surface.blit(flash_surface, (0, 0))

    def _draw_particles(self, surface):
        """Dessine les particules d'etincelles."""
        for p in self.particle_list:
            if p["life"] > 0:
                ratio = p["life"] / p["max_life"]
                alpha = max(0, min(255, int(255 * ratio)))
                size = max(1, int(p["size"] * ratio))
                s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                # Couleur doree/blanche
                r = 255
                g = max(0, min(255, 220 + int(35 * ratio)))
                b = max(0, min(255, int(100 * ratio)))
                pygame.draw.circle(s, (r, g, b, alpha), (size, size), size)
                surface.blit(s, (int(p["x"]) - size, int(p["y"]) - size))

    def _ease_out_back(self, t):
        """Easing avec leger overshoot pour un effet 'pop'."""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)