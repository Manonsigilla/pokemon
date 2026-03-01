"""Ecran pour ajouter un Pokemon dans bdd/pokemon.json ET pokedex.json.

Manon : Corrections apportees :
- Le pokemon est maintenant aussi ajoute dans pokedex.json
- Ajout d'un champ photo (image locale, limitee a 500 Ko)
- Limites de stats basees sur les vrais stats Pokemon
- Labels raccourcis pour que tout rentre dans la fenetre
- Les limites max sont affichees en hint a droite du champ actif
"""

import pygame
import json
import os
import shutil

from states.state import State
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, BG_DARK, WHITE, YELLOW,
                    BLACK, BASE_DIR, get_font)


# ============================================================
# Liste de tous les types Pokemon existants
# ============================================================
ALL_TYPES = [
    "normal", "fire", "water", "electric", "grass", "ice",
    "fighting", "poison", "ground", "flying", "psychic", "bug",
    "rock", "ghost", "dragon", "dark", "steel", "fairy"
]

# ============================================================
# Limites de statistiques (basees sur les stats reelles Gen 1-9)
# ============================================================
STAT_LIMITS = {
    "hp":              {"min": 1, "max": 255},
    "attack":          {"min": 1, "max": 190},
    "defense":         {"min": 1, "max": 230},
    "special-attack":  {"min": 1, "max": 194},
    "special-defense": {"min": 1, "max": 230},
    "speed":           {"min": 1, "max": 200},
}

# ============================================================
# Contraintes pour la photo
# ============================================================
MAX_IMAGE_SIZE_KB = 500
ALLOWED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")
CUSTOM_SPRITES_DIR = os.path.join(BASE_DIR, "assets", "sprites", "custom")


class AddPokemonState(State):
    """Formulaire pour ajouter un Pokemon dans pokemon.json + pokedex.json."""

    def __init__(self, state_manager):
        super().__init__(state_manager)
        self._font_title = None
        self._font_label = None
        self._font_input = None
        self._font_hint = None

    @property
    def font_title(self):
        if self._font_title is None:
            self._font_title = get_font(24)
        return self._font_title

    @property
    def font_label(self):
        if self._font_label is None:
            self._font_label = get_font(16)
        return self._font_label

    @property
    def font_input(self):
        if self._font_input is None:
            self._font_input = get_font(18)
        return self._font_input

    @property
    def font_hint(self):
        if self._font_hint is None:
            self._font_hint = get_font(12)
        return self._font_hint

    def enter(self):
        """Initialise tous les champs du formulaire.

        Manon : les labels sont COURTS pour tenir dans la fenetre.
        Les valeurs max sont affichees en hint a droite du champ actif.
        """
        self.fields = [
            # Manon : labels courts, la limite max est dans "max_hint"
            {"label": "Nom",          "key": "name",            "value": "", "type": "text",        "max_hint": ""},
            {"label": "Type 1",       "key": "type1",           "value": "", "type": "type_select", "max_hint": ""},
            {"label": "Type 2",       "key": "type2",           "value": "", "type": "type_select", "max_hint": "optionnel"},
            {"label": "PV",           "key": "hp",              "value": "", "type": "number",      "max_hint": f"1 - {STAT_LIMITS['hp']['max']}"},
            {"label": "Attaque",      "key": "attack",          "value": "", "type": "number",      "max_hint": f"1 - {STAT_LIMITS['attack']['max']}"},
            {"label": "Defense",      "key": "defense",         "value": "", "type": "number",      "max_hint": f"1 - {STAT_LIMITS['defense']['max']}"},
            {"label": "Atk Spe.",     "key": "special-attack",  "value": "", "type": "number",      "max_hint": f"1 - {STAT_LIMITS['special-attack']['max']}"},
            {"label": "Def Spe.",     "key": "special-defense", "value": "", "type": "number",      "max_hint": f"1 - {STAT_LIMITS['special-defense']['max']}"},
            {"label": "Vitesse",      "key": "speed",           "value": "", "type": "number",      "max_hint": f"1 - {STAT_LIMITS['speed']['max']}"},
            {"label": "Photo",        "key": "photo",           "value": "", "type": "photo",       "max_hint": f"max {MAX_IMAGE_SIZE_KB}Ko"},
        ]
        self.active_field = 0
        self.message = ""
        self.message_timer = 0
        self.type_selector_open = False
        self.type_selector_index = 0
        self.photo_preview = None

        os.makedirs(CUSTOM_SPRITES_DIR, exist_ok=True)

    # ============================================================
    # GESTION DES EVENEMENTS
    # ============================================================
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.type_selector_open:
                        self.type_selector_open = False
                    else:
                        return_to = self.state_manager.shared_data.pop(
                            "add_pokemon_return_to", "title"
                        )
                        self.state_manager.change_state(return_to)
                    return

                if self.type_selector_open:
                    self._handle_type_selector(event)
                    return

                if event.key == pygame.K_TAB or event.key == pygame.K_DOWN:
                    self.active_field = (self.active_field + 1) % len(self.fields)
                elif event.key == pygame.K_UP:
                    self.active_field = (self.active_field - 1) % len(self.fields)
                elif event.key == pygame.K_RETURN:
                    field = self.fields[self.active_field]
                    if field["type"] == "type_select":
                        self.type_selector_open = True
                        self.type_selector_index = 0
                    elif field["type"] == "photo":
                        self._open_file_dialog()
                    else:
                        self._save_pokemon()
                elif event.key == pygame.K_BACKSPACE:
                    field = self.fields[self.active_field]
                    if field["type"] in ("text", "number"):
                        field["value"] = field["value"][:-1]
                elif event.key == pygame.K_DELETE:
                    field = self.fields[self.active_field]
                    if field["type"] == "type_select":
                        field["value"] = ""
                    elif field["type"] == "photo":
                        field["value"] = ""
                        self.photo_preview = None
                else:
                    field = self.fields[self.active_field]
                    char = event.unicode
                    if field["type"] == "text" and (char.isalpha() or char in "-_ "):
                        field["value"] += char
                    elif field["type"] == "number" and char.isdigit():
                        field["value"] += char

    def _handle_type_selector(self, event):
        if event.key == pygame.K_UP:
            self.type_selector_index = (self.type_selector_index - 1) % len(ALL_TYPES)
        elif event.key == pygame.K_DOWN:
            self.type_selector_index = (self.type_selector_index + 1) % len(ALL_TYPES)
        elif event.key == pygame.K_RETURN:
            selected_type = ALL_TYPES[self.type_selector_index]
            self.fields[self.active_field]["value"] = selected_type
            self.type_selector_open = False

    # ============================================================
    # EXPLORATEUR DE FICHIERS (photo)
    # ============================================================
    def _open_file_dialog(self):
        """Ouvre un dialogue de selection de fichier image."""
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            filepath = filedialog.askopenfilename(
                title="Choisir une image pour le Pokemon",
                filetypes=[
                    ("Images", "*.png *.jpg *.jpeg"),
                    ("PNG", "*.png"),
                    ("JPEG", "*.jpg *.jpeg"),
                ]
            )
            root.destroy()

            if not filepath:
                return

            ext = os.path.splitext(filepath)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                self.message = f"Format {ext} non supporte ! (PNG/JPG)"
                self.message_timer = 3.0
                return

            file_size_kb = os.path.getsize(filepath) / 1024
            if file_size_kb > MAX_IMAGE_SIZE_KB:
                self.message = (
                    f"Image trop lourde ! {file_size_kb:.0f}Ko "
                    f"(max {MAX_IMAGE_SIZE_KB}Ko)"
                )
                self.message_timer = 3.0
                return

            for field in self.fields:
                if field["key"] == "photo":
                    field["value"] = filepath
                    break

            # Charger une preview redimensionnee
            try:
                img = pygame.image.load(filepath).convert_alpha()
                max_preview = 64
                ratio = min(max_preview / img.get_width(), max_preview / img.get_height())
                new_w = int(img.get_width() * ratio)
                new_h = int(img.get_height() * ratio)
                self.photo_preview = pygame.transform.scale(img, (new_w, new_h))
            except Exception:
                self.photo_preview = None

            self.message = f"Image OK ({file_size_kb:.0f}Ko)"
            self.message_timer = 2.0

        except ImportError:
            self.message = "tkinter non disponible"
            self.message_timer = 3.0

    # ============================================================
    # SAUVEGARDE (bdd/pokemon.json + pokedex.json)
    # ============================================================
    def _save_pokemon(self):
        """Sauvegarde dans bdd/pokemon.json ET pokedex.json."""
        name = self.fields[0]["value"].strip().lower()
        type1 = self.fields[1]["value"]
        type2 = self.fields[2]["value"]

        if not name:
            self.message = "Le nom est obligatoire !"
            self.message_timer = 3.0
            return
        if not type1:
            self.message = "Le type 1 est obligatoire !"
            self.message_timer = 3.0
            return

        # --- Validation des stats avec limites ---
        stats_keys = ["hp", "attack", "defense", "special-attack", "special-defense", "speed"]
        stats = {}
        for i, key in enumerate(stats_keys):
            field = self.fields[3 + i]
            val = field["value"]
            if not val:
                self.message = f"{field['label']} est obligatoire !"
                self.message_timer = 3.0
                return

            val_int = int(val)
            limit = STAT_LIMITS[key]

            if val_int > limit["max"]:
                self.message = f"{field['label']} trop eleve ! Max = {limit['max']}"
                self.message_timer = 3.0
                return
            if val_int < limit["min"]:
                self.message = f"{field['label']} trop bas ! Min = {limit['min']}"
                self.message_timer = 3.0
                return

            stats[key] = val_int

        types = [type1]
        if type2 and type2 != type1:
            types.append(type2)

        # --- ETAPE 1 : bdd/pokemon.json ---
        pokemon_file = os.path.join(BASE_DIR, "bdd", "pokemon.json")
        with open(pokemon_file, "r", encoding="utf-8") as f:
            all_pokemon = json.load(f)

        for p in all_pokemon:
            if p["name"].lower() == name:
                self.message = f"{name} existe deja !"
                self.message_timer = 3.0
                return

        max_id = max((p["id"] for p in all_pokemon), default=0)
        new_id = max_id + 1

        # --- Gerer la photo custom ---
        photo_field_value = ""
        for field in self.fields:
            if field["key"] == "photo":
                photo_field_value = field["value"]
                break

        custom_sprite_path = ""
        if photo_field_value and os.path.exists(photo_field_value):
            ext = os.path.splitext(photo_field_value)[1].lower()
            dest_filename = f"{name.replace(' ', '_')}_{new_id}{ext}"
            dest_path = os.path.join(CUSTOM_SPRITES_DIR, dest_filename)
            try:
                shutil.copy2(photo_field_value, dest_path)
                custom_sprite_path = dest_path
            except Exception as e:
                print(f"Erreur copie image : {e}")

        # --- Sprites ---
        if custom_sprite_path:
            sprites = {
                "front_default": custom_sprite_path,
                "back_default": custom_sprite_path,
                "front_shiny": custom_sprite_path,
                "official_artwork": custom_sprite_path
            }
        else:
            sprites = {
                "front_default": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{new_id}.png",
                "back_default": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/{new_id}.png",
                "front_shiny": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{new_id}.png",
                "official_artwork": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{new_id}.png"
            }

        new_pokemon_bdd = {
            "id": new_id,
            "name": name,
            "types": types,
            "stats": stats,
            "sprites": sprites,
            "moves": ["tackle", "scratch", "pound", "headbutt"],
            "weight": 100,
            "height": 10
        }

        all_pokemon.append(new_pokemon_bdd)
        with open(pokemon_file, "w", encoding="utf-8") as f:
            json.dump(all_pokemon, f, ensure_ascii=False, indent=4)

        # --- ETAPE 2 : pokedex.json ---
        pokedex_file = os.path.join(BASE_DIR, "pokedex.json")
        if os.path.exists(pokedex_file):
            try:
                with open(pokedex_file, "r", encoding="utf-8") as f:
                    pokedex_data = json.load(f)
            except Exception:
                pokedex_data = {"pokemon": [], "count": 0}
        else:
            pokedex_data = {"pokemon": [], "count": 0}

        already_in = False
        for entry in pokedex_data.get("pokemon", []):
            if entry.get("id") == new_id or entry.get("name", "").lower() == name:
                already_in = True
                break

        if not already_in:
            pokedex_entry = {
                "id": new_id,
                "name": name,
                "type": types,
                "hp": stats["hp"],
                "attack": stats["attack"],
                "defense": stats["defense"],
                # Manon : on stocke le chemin du sprite custom pour l'affichage
                "sprite": custom_sprite_path if custom_sprite_path else sprites["front_default"]
            }
            if "pokemon" not in pokedex_data:
                pokedex_data["pokemon"] = []
            pokedex_data["pokemon"].append(pokedex_entry)
            pokedex_data["count"] = len(pokedex_data["pokemon"])

            with open(pokedex_file, "w", encoding="utf-8") as f:
                json.dump(pokedex_data, f, ensure_ascii=False, indent=4)

        self.message = f"{name.title()} (#{new_id}) ajoute !"
        self.message_timer = 3.0

        for field in self.fields:
            field["value"] = ""
        self.photo_preview = None

    # ============================================================
    # UPDATE
    # ============================================================
    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0 and "ajoute" in self.message:
                return_to = self.state_manager.shared_data.pop(
                    "add_pokemon_return_to", "title"
                )
                self.state_manager.change_state(return_to)

    # ============================================================
    # DESSIN DU FORMULAIRE
    # ============================================================
    def draw(self, surface):
        surface.fill(BG_DARK)

        title = self.font_title.render("AJOUTER UN POKEMON", True, YELLOW)
        surface.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 15))

        start_y = 55
        field_height = 42

        for i, field in enumerate(self.fields):
            y = start_y + i * field_height
            is_active = (i == self.active_field)

            # --- Label court a gauche ---
            label_color = YELLOW if is_active else (180, 180, 180)
            label = self.font_label.render(field["label"] + " :", True, label_color)
            surface.blit(label, (40, y + 5))

            # --- Zone de saisie (commence plus a droite pour les labels courts) ---
            # Manon : on laisse 200px pour le label au lieu de 250
            input_x = 200
            input_rect = pygame.Rect(input_x, y, 280, 32)
            border_color = YELLOW if is_active else (100, 100, 100)
            pygame.draw.rect(surface, (50, 50, 60), input_rect, border_radius=5)
            pygame.draw.rect(surface, border_color, input_rect, 2, border_radius=5)

            # --- Valeur affichee ---
            if field["type"] == "photo":
                if field["value"]:
                    display_value = os.path.basename(field["value"])
                    if len(display_value) > 28:
                        display_value = display_value[:25] + "..."
                    value_color = (100, 220, 100)
                else:
                    display_value = "(aucune)"
                    value_color = (100, 100, 100)
            else:
                display_value = field["value"] if field["value"] else "(vide)"
                value_color = WHITE if field["value"] else (100, 100, 100)

            value_text = self.font_input.render(display_value, True, value_color)
            surface.blit(value_text, (input_rect.x + 8, input_rect.y + 6))

            # --- Curseur clignotant ---
            if is_active and field["type"] in ("text", "number"):
                cursor_x = input_rect.x + 8 + value_text.get_width() + 2
                if pygame.time.get_ticks() % 1000 < 500:
                    pygame.draw.line(
                        surface, WHITE,
                        (cursor_x, y + 6), (cursor_x, y + 28), 2
                    )

            # --- Hint a droite du champ actif ---
            # Manon : affiche les limites/instructions a droite du champ
            if is_active:
                hint_text = ""
                if field["type"] == "type_select":
                    hint_text = "Entree=choisir Suppr=vider"
                elif field["type"] == "photo":
                    hint_text = "Entree=parcourir Suppr=retirer"
                elif field.get("max_hint"):
                    hint_text = field["max_hint"]

                if hint_text:
                    hint_surf = self.font_hint.render(hint_text, True, (150, 150, 150))
                    surface.blit(hint_surf, (input_rect.right + 10, y + 10))

        # --- Preview photo ---
        if self.photo_preview:
            preview_x = SCREEN_WIDTH - 90
            preview_y = start_y + (len(self.fields) - 1) * field_height - 10
            preview_rect = pygame.Rect(
                preview_x - 4, preview_y - 4,
                self.photo_preview.get_width() + 8,
                self.photo_preview.get_height() + 8
            )
            pygame.draw.rect(surface, (80, 80, 90), preview_rect, border_radius=4)
            pygame.draw.rect(surface, YELLOW, preview_rect, 2, border_radius=4)
            surface.blit(self.photo_preview, (preview_x, preview_y))

        # --- Selecteur de type ---
        if self.type_selector_open:
            self._draw_type_selector(surface)

        # --- Message ---
        if self.message_timer > 0:
            is_error = any(w in self.message for w in ["obligatoire", "existe", "trop", "non supporte", "lourde", "bas"])
            msg_color = (255, 80, 80) if is_error else (80, 255, 80)
            msg = self.font_label.render(self.message, True, msg_color)
            surface.blit(msg, ((SCREEN_WIDTH - msg.get_width()) // 2, SCREEN_HEIGHT - 80))

        # --- Barre d'aide ---
        hint = self.font_hint.render(
            "TAB/Fleches = naviguer | Entree = valider | Echap = retour",
            True, (120, 120, 120)
        )
        surface.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, SCREEN_HEIGHT - 30))

    # ============================================================
    # SELECTEUR DE TYPE (popup)
    # ============================================================
    def _draw_type_selector(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        list_width = 200
        list_height = 400
        list_x = (SCREEN_WIDTH - list_width) // 2
        list_y = (SCREEN_HEIGHT - list_height) // 2

        pygame.draw.rect(surface, (40, 40, 50),
                        (list_x, list_y, list_width, list_height), border_radius=8)
        pygame.draw.rect(surface, YELLOW,
                        (list_x, list_y, list_width, list_height), 2, border_radius=8)

        title = self.font_label.render("Choisir un type", True, YELLOW)
        surface.blit(title, (list_x + (list_width - title.get_width()) // 2, list_y + 5))

        visible_count = 16
        start_index = max(0, self.type_selector_index - visible_count // 2)
        start_index = min(start_index, max(0, len(ALL_TYPES) - visible_count))

        for i in range(visible_count):
            idx = start_index + i
            if idx >= len(ALL_TYPES):
                break
            ty = ALL_TYPES[idx]
            item_y = list_y + 30 + i * 22
            is_selected = (idx == self.type_selector_index)
            if is_selected:
                pygame.draw.rect(surface, (80, 80, 100),
                                (list_x + 5, item_y, list_width - 10, 20), border_radius=3)
            color = YELLOW if is_selected else WHITE
            text = self.font_label.render(ty.upper(), True, color)
            surface.blit(text, (list_x + 15, item_y + 2))