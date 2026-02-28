import pygame
import json
import os
from states.state import State
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, BG_DARK, WHITE, YELLOW, get_font, BASE_DIR, BTN_AJOUT, BTN_AJOUT_HOVER)
from ui.sprite_loader import SpriteLoader
from ui.button import Button
from ui.sound_manager import sound_manager


class PokedexState(State):
    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.sprite_loader = SpriteLoader()
        self.font_title = None
        self.font_info = None
        self.pokedex_data = []
        self.sprites_cache = {}
        self.return_to = "title"
        self.add_button = None
        self.scroll_offset = 0
        self.max_scroll = 0

    def enter(self):
        print("Entre dans PokedexState")
        self.font_title = get_font(28)
        self.font_info = get_font(18)
        self.return_to = self.state_manager.shared_data.pop("pokedex_return_to", "title")

        # Charger le pokedex
        pokedex_file = os.path.join(BASE_DIR, "pokedex.json")
        self.pokedex_data = []
        if os.path.exists(pokedex_file):
            try:
                with open(pokedex_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.pokedex_data = data.get("pokemon", [])
            except Exception as e:
                print(f"Erreur pokedex: {e}")

        # Charger les sprites
        for pk in self.pokedex_data:
            sprite_url = pk.get("sprite") or pk.get("front_sprite_path")
            name = pk.get("name", "???")
            if sprite_url and name not in self.sprites_cache:
                try:
                    surf = self.sprite_loader.load_sprite(sprite_url, scale=2)
                    self.sprites_cache[name] = surf
                except Exception:
                    pass

        # Bouton "Ajouter un Pokemon"
        btn_width = 250
        btn_height = 40
        self.add_button = Button(
            SCREEN_WIDTH - btn_width - 20, 10,
            btn_width, btn_height,
            image_normal=BTN_AJOUT,
            image_hover=BTN_AJOUT_HOVER,
            hide_text=True
        )

        # Calculer le scroll max
        self._calc_max_scroll()

    def _calc_max_scroll(self):
        """Calcule la hauteur totale du contenu pour le scroll."""
        # Compter les pokemon uniques
        seen = set()
        count = 0
        for pk in self.pokedex_data:
            name = pk.get("name", "???").capitalize()
            if name not in seen:
                seen.add(name)
                count += 1

        rows = (count + 2) // 3  # 3 colonnes
        content_height = 80 + rows * 120 + 60  # titre + grille + marge
        self.max_scroll = max(0, content_height - SCREEN_HEIGHT)

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        self.add_button.check_hover(mouse_pos)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    self.state_manager.change_state(self.return_to)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.add_button.check_click(mouse_pos, True):
                    sound_manager.play_select()
                    # Garder le retour pour revenir au pokedex apres l'ajout
                    self.state_manager.shared_data["add_pokemon_return_to"] = "pokedex"
                    self.state_manager.shared_data["pokedex_return_to"] = self.return_to
                    self.state_manager.change_state("add_pokemon")

            if event.type == pygame.MOUSEWHEEL:
                self.scroll_offset -= event.y * 30
                self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill(BG_DARK)

        # Bandeau du haut (fixe)
        pygame.draw.rect(screen, (40, 40, 50), (0, 0, SCREEN_WIDTH, 60))
        pygame.draw.rect(screen, (80, 80, 90), (0, 57, SCREEN_WIDTH, 3))

        # Titre
        title = self.font_title.render("POKEDEX", True, YELLOW)
        screen.blit(title, (20, 15))

        # Compteur
        seen = set()
        for pk in self.pokedex_data:
            seen.add(pk.get("name", "???").capitalize())
        count_text = self.font_info.render(f"{len(seen)} Pokemon", True, (180, 180, 180))
        screen.blit(count_text, (20, 38))

        # Bouton Ajouter (dans le bandeau)
        self.add_button.draw(screen)

        # Zone de contenu scrollable
        content_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - 60))
        content_surface.fill(BG_DARK)

        # Grille des Pokemon
        start_x, start_y = 50, 20
        col, row = 0, 0
        max_col = 3

        if not self.pokedex_data:
            msg = self.font_info.render("Aucun Pokemon enregistre.", True, WHITE)
            content_surface.blit(msg, ((SCREEN_WIDTH - msg.get_width()) // 2, 200))
        else:
            drawn = set()
            for pk in self.pokedex_data:
                name = pk.get("name", "???").capitalize()
                if name in drawn:
                    continue
                drawn.add(name)

                x = start_x + col * 220
                y = start_y + row * 120 - self.scroll_offset

                # Ne dessiner que si visible
                if y + 120 > 0 and y < SCREEN_HEIGHT - 60:
                    # Fond de la carte
                    card_rect = pygame.Rect(x - 10, y, 200, 110)
                    pygame.draw.rect(content_surface, (50, 50, 60), card_rect, border_radius=8)
                    pygame.draw.rect(content_surface, (80, 80, 90), card_rect, 2, border_radius=8)

                    # Sprite
                    sprite = self.sprites_cache.get(name.lower())
                    if sprite:
                        sx = x + (80 - sprite.get_width()) // 2
                        content_surface.blit(sprite, (sx, y + 5))

                    # Nom
                    name_surf = self.font_info.render(name, True, WHITE)
                    content_surface.blit(name_surf, (x + 85, y + 10))

                    # Types
                    types = pk.get("type", [])
                    type_text = ", ".join(t.title() for t in types)
                    type_surf = get_font(12).render(type_text, True, (180, 180, 180))
                    content_surface.blit(type_surf, (x + 85, y + 35))

                    # Stats
                    hp = pk.get("hp", "?")
                    atk = pk.get("attack", "?")
                    dfn = pk.get("defense", "?")
                    stats_text = f"PV:{hp}  ATK:{atk}  DEF:{dfn}"
                    stats_surf = get_font(11).render(stats_text, True, (150, 150, 150))
                    content_surface.blit(stats_surf, (x + 85, y + 55))

                    # ID
                    id_text = get_font(10).render(f"#{pk.get('id', '?')}", True, (120, 120, 120))
                    content_surface.blit(id_text, (x + 85, y + 80))

                col += 1
                if col >= max_col:
                    col = 0
                    row += 1

        screen.blit(content_surface, (0, 60))

        # Instruction retour
        hint_bg = pygame.Surface((SCREEN_WIDTH, 30), pygame.SRCALPHA)
        hint_bg.fill((0, 0, 0, 150))
        screen.blit(hint_bg, (0, SCREEN_HEIGHT - 30))
        hint = get_font(12).render("ECHAP pour revenir | Molette pour defiler", True, (150, 150, 150))
        screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, SCREEN_HEIGHT - 25))

        # Scrollbar
        if self.max_scroll > 0:
            bar_height = max(30, int((SCREEN_HEIGHT - 90) * (SCREEN_HEIGHT - 60) / (SCREEN_HEIGHT - 60 + self.max_scroll)))
            bar_y = 60 + int((SCREEN_HEIGHT - 90 - bar_height) * (self.scroll_offset / self.max_scroll))
            pygame.draw.rect(screen, (60, 60, 70), (SCREEN_WIDTH - 10, 60, 6, SCREEN_HEIGHT - 90), border_radius=3)
            pygame.draw.rect(screen, YELLOW, (SCREEN_WIDTH - 10, bar_y, 6, bar_height), border_radius=3)