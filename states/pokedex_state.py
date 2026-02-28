import pygame
import json
import os
from states.state import State
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, BG_DARK, WHITE, YELLOW,
                    get_font, BASE_DIR, BTN_AJOUT, BTN_AJOUT_HOVER,
                    BG_POKEDEX, POKEDEX_TITLE_IMG)
from ui.sprite_loader import SpriteLoader
from ui.button import Button
from ui.sound_manager import sound_manager


class PokedexState(State):
    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.sprite_loader = SpriteLoader()
        self.pokedex_data = []
        self.sprites_cache = {}
        self.return_to = "title"
        self.add_button = None
        self.scroll_offset = 0
        self.max_scroll = 0
        self.bg_image = None
        self.title_image = None
        self.bdd_pokemon = []  # Donnees completes depuis bdd/pokemon.json

    def enter(self):
        print("Entre dans PokedexState")
        self.return_to = self.state_manager.shared_data.pop("pokedex_return_to", "title")

        # ============ BACKGROUND ============
        try:
            bg = pygame.image.load(BG_POKEDEX).convert()
            self.bg_image = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception as e:
            print(f"[Pokedex] Fond introuvable ({e}), fallback couleur")
            self.bg_image = None

        # ============ IMAGE TITRE ============
        try:
            title_img = pygame.image.load(POKEDEX_TITLE_IMG).convert_alpha()
            max_title_width = 350
            ratio = min(max_title_width / title_img.get_width(), 1.0)
            new_w = int(title_img.get_width() * ratio)
            new_h = int(title_img.get_height() * ratio)
            self.title_image = pygame.transform.scale(title_img, (new_w, new_h))
        except Exception as e:
            print(f"[Pokedex] Image titre introuvable ({e}), fallback texte")
            self.title_image = None

        # ============ CHARGER BDD POKEMON (pour les sprites) ============
        bdd_file = os.path.join(BASE_DIR, "bdd", "pokemon.json")
        self.bdd_pokemon = []
        if os.path.exists(bdd_file):
            try:
                with open(bdd_file, "r", encoding="utf-8") as f:
                    self.bdd_pokemon = json.load(f)
            except Exception:
                pass

        # ============ CHARGER LE POKEDEX ============
        pokedex_file = os.path.join(BASE_DIR, "pokedex.json")
        self.pokedex_data = []
        if os.path.exists(pokedex_file):
            try:
                with open(pokedex_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.pokedex_data = data.get("pokemon", [])
            except Exception as e:
                print(f"Erreur pokedex: {e}")

        # ============ CHARGER LES SPRITES ============
        self._load_sprites()

        # ============ BOUTON AJOUTER ============
        btn_width = 250
        btn_height = 40
        self.add_button = Button(
            SCREEN_WIDTH - btn_width - 20, 30,
            btn_width, btn_height,
            image_normal=BTN_AJOUT,
            image_hover=BTN_AJOUT_HOVER,
            hide_text=True
        )

        self.scroll_offset = 0
        self._calc_max_scroll()

    def _load_sprites(self):
        """Charge les sprites depuis les URLs de bdd/pokemon.json via le cache."""
        import urllib.request

        cache_dir = os.path.join(BASE_DIR, "cache", "starter_sprites")
        os.makedirs(cache_dir, exist_ok=True)

        for pk in self.pokedex_data:
            pk_id = pk.get("id")
            name = pk.get("name", "???").lower()

            if name in self.sprites_cache:
                continue

            # Chercher dans bdd/pokemon.json
            bdd_entry = None
            for bp in self.bdd_pokemon:
                if bp["id"] == pk_id:
                    bdd_entry = bp
                    break

            if not bdd_entry:
                continue

            sprite_url = bdd_entry.get("sprites", {}).get("front_default", "")
            if not sprite_url:
                continue

            # Telecharger ou utiliser le cache
            filename = sprite_url.split("/")[-1]
            filepath = os.path.join(cache_dir, filename)

            if not os.path.exists(filepath):
                try:
                    urllib.request.urlretrieve(sprite_url, filepath)
                except Exception:
                    continue

            if os.path.exists(filepath):
                try:
                    sprite = self.sprite_loader.load_sprite(filepath, scale=2)
                    self.sprites_cache[name] = sprite
                except Exception:
                    pass

    def _calc_max_scroll(self):
        seen = set()
        count = 0
        for pk in self.pokedex_data:
            name = pk.get("name", "???").capitalize()
            if name not in seen:
                seen.add(name)
                count += 1

        max_col = 3
        rows = (count + max_col - 1) // max_col
        card_height = 140
        card_spacing = 15
        content_height = rows * (card_height + card_spacing) + 20
        available_height = SCREEN_HEIGHT - 110 - 35  # header - footer
        self.max_scroll = max(0, content_height - available_height)

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
                    self.state_manager.shared_data["add_pokemon_return_to"] = "pokedex"
                    self.state_manager.shared_data["pokedex_return_to"] = self.return_to
                    self.state_manager.change_state("add_pokemon")

            if event.type == pygame.MOUSEWHEEL:
                self.scroll_offset -= event.y * 30
                self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

    def update(self, dt):
        pass

    def draw(self, screen):
        # ============ BACKGROUND ============
        if self.bg_image:
            screen.blit(self.bg_image, (0, 0))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill(BG_DARK)

        # ============ BANDEAU DU HAUT ============
        header_height = 120
        header_bg = pygame.Surface((SCREEN_WIDTH, header_height), pygame.SRCALPHA)
        header_bg.fill((30, 30, 40, 200))
        screen.blit(header_bg, (0, 0))
        pygame.draw.line(screen, (80, 80, 90), (0, header_height - 1), (SCREEN_WIDTH, header_height - 1), 2)

        # ============ TITRE — A GAUCHE ============
        if self.title_image:
            title_x = 20
            title_y = 10
            screen.blit(self.title_image, (title_x, title_y))
            compteur_y = title_y + self.title_image.get_height() + 5
        else:
            font_title = get_font(28)
            title = font_title.render("POKEDEX", True, YELLOW)
            screen.blit(title, (20, 10))
            compteur_y = 45

        # ============ COMPTEUR — SOUS LE TITRE, A GAUCHE ============
        font_info = get_font(14)
        seen = set()
        for pk in self.pokedex_data:
            seen.add(pk.get("name", "???").capitalize())
        count_text = font_info.render(f"{len(seen)} Pokemon rencontres", True, (180, 180, 180))
        screen.blit(count_text, (20, compteur_y))

        # ============ BOUTON AJOUTER — A DROITE ============
        self.add_button.rect.x = SCREEN_WIDTH - self.add_button.rect.width - 20
        self.add_button.rect.y = (header_height - self.add_button.rect.height) // 2
        self.add_button.draw(screen)

        # ============ ZONE DE CONTENU ============
        content_y = header_height + 10
        content_height = SCREEN_HEIGHT - content_y - 35

        content_surface = pygame.Surface((SCREEN_WIDTH, content_height), pygame.SRCALPHA)
        content_surface.fill((0, 0, 0, 0))

        # ============ GRILLE DES POKEMON ============
        max_col = 3
        card_width = 250
        card_height = 160
        card_spacing_x = 10
        card_spacing_y = 15

        # Centrer la grille horizontalement
        total_grid_width = max_col * card_width + (max_col - 1) * card_spacing_x
        grid_start_x = (SCREEN_WIDTH - total_grid_width) // 2

        font_name = get_font(14)
        font_type = get_font(11)
        font_stats = get_font(10)
        font_id = get_font(10)

        if not self.pokedex_data:
            msg = font_name.render("Aucun Pokemon enregistre.", True, WHITE)
            content_surface.blit(msg, ((SCREEN_WIDTH - msg.get_width()) // 2, content_height // 2 - 20))
        else:
            drawn = set()
            col = 0
            row = 0

            for pk in self.pokedex_data:
                name = pk.get("name", "???").capitalize()
                if name in drawn:
                    continue
                drawn.add(name)

                x = grid_start_x + col * (card_width + card_spacing_x)
                y = 10 + row * (card_height + card_spacing_y) - self.scroll_offset

                if y + card_height > 0 and y < content_height:
                    # ---- Fond de la carte ----
                    card_rect = pygame.Rect(x, y, card_width, card_height)
                    card_bg = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
                    card_bg.fill((45, 45, 55, 210))
                    content_surface.blit(card_bg, (x, y))
                    pygame.draw.rect(content_surface, (90, 90, 100), card_rect, 2, border_radius=8)

                    # ---- Sprite a gauche, centre verticalement ----
                    sprite = self.sprites_cache.get(name.lower())
                    sprite_area_width = 80

                    if sprite:
                        sx = x + (sprite_area_width - sprite.get_width()) // 2
                        sy = y + (card_height - sprite.get_height()) // 2
                        content_surface.blit(sprite, (sx, sy))
                    else:
                        # Placeholder gris
                        placeholder = pygame.Surface((48, 48), pygame.SRCALPHA)
                        placeholder.fill((80, 80, 80, 100))
                        px = x + (sprite_area_width - 48) // 2
                        py = y + (card_height - 48) // 2
                        content_surface.blit(placeholder, (px, py))
                        no_sprite = font_id.render("?", True, (120, 120, 120))
                        content_surface.blit(no_sprite, (px + 20, py + 15))

                    # ---- Texte a droite du sprite ----
                    text_x = x + sprite_area_width + 10
                    text_max_width = card_width - sprite_area_width - 20

                    # Nom
                    name_display = name
                    name_surf = font_name.render(name, True, WHITE)
                    # Tronquer si trop long
                    if name_surf.get_width() > text_max_width:
                        while name_surf.get_width() > text_max_width and len(name) > 3:
                            name = name[:-1]
                            name_surf = font_name.render(name + "..", True, WHITE)
                    name_x = text_x + (text_max_width - name_surf.get_width()) // 2
                    content_surface.blit(name_surf, (text_x, y + 10))

                    # ID
                    id_text = font_id.render(f"#{pk.get('id', '?'):03d}", True, (150, 150, 150))
                    content_surface.blit(id_text, (text_x, y + 32))

                    # Types
                    types = pk.get("type", [])
                    type_text = " / ".join(t.title() for t in types)
                    type_surf = font_type.render(type_text, True, (180, 180, 180))
                    if type_surf.get_width() > text_max_width:
                        type_text_short = type_text
                        while type_surf.get_width() > text_max_width and len(type_text_short) > 3:
                            type_text_short = type_text_short[:-1]
                            type_surf = font_type.render(type_text_short + "..", True, (180, 180, 180))
                    content_surface.blit(type_surf, (text_x, y + 50))

                    # Stats sur 2 lignes
                    hp = pk.get("hp", "?")
                    atk = pk.get("attack", "?")
                    dfn = pk.get("defense", "?")

                    line1 = f"PV: {hp}  ATK: {atk}"
                    line2 = f"DEF: {dfn}"

                    stats1_surf = font_stats.render(line1, True, (140, 140, 140))
                    stats2_surf = font_stats.render(line2, True, (140, 140, 140))
                    content_surface.blit(stats1_surf, (text_x, y + 75))
                    content_surface.blit(stats2_surf, (text_x, y + 92))

                    # Bordure coloree a gauche selon le type principal
                    from config import TYPE_COLORS
                    if types:
                        type_color = TYPE_COLORS.get(types[0], (150, 150, 150))
                        pygame.draw.rect(content_surface, type_color, (x, y, 4, card_height), border_radius=2)

                col += 1
                if col >= max_col:
                    col = 0
                    row += 1

        screen.blit(content_surface, (0, content_y))

        # ============ BARRE DU BAS ============
        hint_bg = pygame.Surface((SCREEN_WIDTH, 35), pygame.SRCALPHA)
        hint_bg.fill((0, 0, 0, 180))
        screen.blit(hint_bg, (0, SCREEN_HEIGHT - 35))
        font_hint = get_font(12)
        hint = font_hint.render("ECHAP pour revenir | Molette pour defiler", True, (150, 150, 150))
        screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, SCREEN_HEIGHT - 27))

        # ============ SCROLLBAR ============
        if self.max_scroll > 0:
            bar_total_height = content_height - 10
            bar_height = max(30, int(bar_total_height * content_height / (content_height + self.max_scroll)))
            bar_y = content_y + 5 + int((bar_total_height - bar_height) * (self.scroll_offset / self.max_scroll))
            pygame.draw.rect(screen, (60, 60, 70), (SCREEN_WIDTH - 12, content_y + 5, 6, bar_total_height), border_radius=3)
            pygame.draw.rect(screen, YELLOW, (SCREEN_WIDTH - 12, bar_y, 6, bar_height), border_radius=3)