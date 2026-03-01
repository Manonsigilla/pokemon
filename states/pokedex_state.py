import pygame
import json
import os
import requests
from io import BytesIO
from states.state import State
from config import SCREEN_WIDTH, SCREEN_HEIGHT, BG_DARK, WHITE, YELLOW, get_font, BASE_DIR
from ui.sprite_loader import SpriteLoader

class PokedexState(State):
    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.sprite_loader = SpriteLoader()
        self.font_title = get_font(28)
        self.font_info = get_font(18)
        self.pokedex_data = []
        self.sprites_cache = {}

    def enter(self):
        print("Entré dans PokedexState")
        pokedex_file = os.path.join(BASE_DIR, "pokedex.json")
        if os.path.exists(pokedex_file):
            try:
                with open(pokedex_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.pokedex_data = data.get("pokemon", [])
            except Exception as e:
                print(f"Erreur pokedex: {e}")
                
        # Load sprites manually if they don't exist in local cache?
        # Sprite loader already does this via URL or Cache.
        for pk in self.pokedex_data:
            sprite_url = pk.get("sprite") or pk.get("front_sprite_path")
            name = pk.get("name", "???")
            if sprite_url and name not in self.sprites_cache:
                try:
                    surf = self.sprite_loader.load_sprite(sprite_url, scale=2)
                    self.sprites_cache[name] = surf
                except Exception:
                    pass

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    # Retour a la carte
                    self.state_manager.change_state("map")

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill(BG_DARK)
        
        # Titre
        title = self.font_title.render("POKEDEX", True, YELLOW)
        screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 20))
        
        # Grid variables
        start_x, start_y = 50, 80
        col, row = 0, 0
        max_col = 3
        
        if not self.pokedex_data:
            msg = self.font_info.render("Aucun Pokémon enregistré.", True, WHITE)
            screen.blit(msg, ((SCREEN_WIDTH - msg.get_width()) // 2, SCREEN_HEIGHT // 2))
        else:
            # On affiche les Pokémons uniques
            seen = set()
            for pk in self.pokedex_data:
                name = pk.get("name", "???").capitalize()
                if name in seen:
                    continue
                seen.add(name)
                
                x = start_x + col * 150
                y = start_y + row * 120
                
                # Sprite
                sprite = self.sprites_cache.get(name.lower())
                if sprite:
                    # Centrer le sprite
                    sx = x + (100 - sprite.get_width()) // 2
                    screen.blit(sprite, (sx, y))
                    
                # Nom
                name_surf = self.font_info.render(name, True, WHITE)
                nx = x + (100 - name_surf.get_width()) // 2
                screen.blit(name_surf, (nx, y + 80))
                
                col += 1
                if col >= max_col:
                    col = 0
                    row += 1

        # Instruction retour
        hint = self.font_info.render("ECHAP pour revenir", True, (150, 150, 150))
        screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, SCREEN_HEIGHT - 40))
