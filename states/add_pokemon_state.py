"""Ecran pour ajouter un Pokemon dans bdd/pokemon.json."""

import pygame
import json
import os

from states.state import State
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, BG_DARK, WHITE, YELLOW,
                    BLACK, BASE_DIR, get_font)


ALL_TYPES = [
    "normal", "fire", "water", "electric", "grass", "ice",
    "fighting", "poison", "ground", "flying", "psychic", "bug",
    "rock", "ghost", "dragon", "dark", "steel", "fairy"
]


class AddPokemonState(State):
    """Formulaire pour ajouter un Pokemon dans pokemon.json."""

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
        self.fields = [
            {"label": "Nom", "key": "name", "value": "", "type": "text"},
            {"label": "Type 1", "key": "type1", "value": "", "type": "type_select"},
            {"label": "Type 2 (optionnel)", "key": "type2", "value": "", "type": "type_select"},
            {"label": "PV", "key": "hp", "value": "", "type": "number"},
            {"label": "Attaque", "key": "attack", "value": "", "type": "number"},
            {"label": "Defense", "key": "defense", "value": "", "type": "number"},
            {"label": "Attaque Spe.", "key": "special-attack", "value": "", "type": "number"},
            {"label": "Defense Spe.", "key": "special-defense", "value": "", "type": "number"},
            {"label": "Vitesse", "key": "speed", "value": "", "type": "number"},
        ]
        self.active_field = 0
        self.message = ""
        self.message_timer = 0
        self.type_selector_open = False
        self.type_selector_index = 0

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.type_selector_open:
                        self.type_selector_open = False
                    else:
                        # Revenir au pokedex ou au titre
                        return_to = self.state_manager.shared_data.pop("add_pokemon_return_to", "title")
                        if return_to == "pokedex":
                            # Recharger le pokedex_return_to pour que le pokedex sache ou revenir
                            pass  # deja dans shared_data
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
                    else:
                        self._save_pokemon()
                elif event.key == pygame.K_BACKSPACE:
                    field = self.fields[self.active_field]
                    if field["type"] != "type_select":
                        field["value"] = field["value"][:-1]
                elif event.key == pygame.K_DELETE:
                    # Permet de vider un champ type
                    field = self.fields[self.active_field]
                    if field["type"] == "type_select":
                        field["value"] = ""
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

    def _save_pokemon(self):
        name = self.fields[0]["value"].strip().lower()
        type1 = self.fields[1]["value"]
        type2 = self.fields[2]["value"]

        if not name:
            self.message = "Erreur : le nom est obligatoire !"
            self.message_timer = 3.0
            return

        if not type1:
            self.message = "Erreur : le type 1 est obligatoire !"
            self.message_timer = 3.0
            return

        stats_keys = ["hp", "attack", "defense", "special-attack", "special-defense", "speed"]
        stats = {}
        for i, key in enumerate(stats_keys):
            val = self.fields[3 + i]["value"]
            if not val:
                self.message = f"Erreur : {self.fields[3 + i]['label']} est obligatoire !"
                self.message_timer = 3.0
                return
            stats[key] = int(val)

        types = [type1]
        if type2 and type2 != type1:
            types.append(type2)

        pokemon_file = os.path.join(BASE_DIR, "bdd", "pokemon.json")
        with open(pokemon_file, "r", encoding="utf-8") as f:
            all_pokemon = json.load(f)

        for p in all_pokemon:
            if p["name"].lower() == name:
                self.message = f"Erreur : {name} existe deja !"
                self.message_timer = 3.0
                return

        max_id = max((p["id"] for p in all_pokemon), default=0)
        new_id = max_id + 1

        new_pokemon = {
            "id": new_id,
            "name": name,
            "types": types,
            "stats": stats,
            "sprites": {
                "front_default": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{new_id}.png",
                "back_default": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/{new_id}.png",
                "front_shiny": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{new_id}.png",
                "official_artwork": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{new_id}.png"
            },
            "moves": ["tackle", "scratch", "pound", "headbutt"],
            "weight": 100,
            "height": 10
        }

        all_pokemon.append(new_pokemon)
        with open(pokemon_file, "w", encoding="utf-8") as f:
            json.dump(all_pokemon, f, ensure_ascii=False, indent=4)

        self.message = f"{name.title()} (#{new_id}) ajoute avec succes !"
        self.message_timer = 3.0

        for field in self.fields:
            field["value"] = ""

    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer -= dt
            # Retour auto au pokedex apres un ajout reussi
            if self.message_timer <= 0 and "succes" in self.message:
                return_to = self.state_manager.shared_data.pop("add_pokemon_return_to", "title")
                self.state_manager.change_state(return_to)

    def draw(self, surface):
        surface.fill(BG_DARK)

        title = self.font_title.render("AJOUTER UN POKEMON", True, YELLOW)
        surface.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 20))

        start_y = 70
        field_height = 45

        for i, field in enumerate(self.fields):
            y = start_y + i * field_height
            is_active = (i == self.active_field)

            label_color = YELLOW if is_active else (180, 180, 180)
            label = self.font_label.render(field["label"] + " :", True, label_color)
            surface.blit(label, (40, y + 5))

            input_rect = pygame.Rect(250, y, 250, 32)
            border_color = YELLOW if is_active else (100, 100, 100)
            pygame.draw.rect(surface, (50, 50, 60), input_rect, border_radius=5)
            pygame.draw.rect(surface, border_color, input_rect, 2, border_radius=5)

            display_value = field["value"] if field["value"] else "(vide)"
            value_color = WHITE if field["value"] else (100, 100, 100)
            value_text = self.font_input.render(display_value, True, value_color)
            surface.blit(value_text, (input_rect.x + 8, input_rect.y + 6))

            if is_active and field["type"] != "type_select":
                cursor_x = input_rect.x + 8 + value_text.get_width() + 2
                if pygame.time.get_ticks() % 1000 < 500:
                    pygame.draw.line(surface, WHITE, (cursor_x, y + 6), (cursor_x, y + 28), 2)

            if field["type"] == "type_select" and is_active:
                hint = self.font_hint.render("Entree = choisir | Suppr = vider", True, (150, 150, 150))
                surface.blit(hint, (510, y + 10))

        if self.type_selector_open:
            self._draw_type_selector(surface)

        if self.message_timer > 0:
            is_error = "Erreur" in self.message
            msg_color = (255, 80, 80) if is_error else (80, 255, 80)
            msg = self.font_label.render(self.message, True, msg_color)
            surface.blit(msg, ((SCREEN_WIDTH - msg.get_width()) // 2, SCREEN_HEIGHT - 80))

        hint = self.font_hint.render(
            "TAB/Fleches = naviguer | Entree = valider | Echap = retour", True, (120, 120, 120)
        )
        surface.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, SCREEN_HEIGHT - 30))

    def _draw_type_selector(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        list_width = 200
        list_height = 400
        list_x = (SCREEN_WIDTH - list_width) // 2
        list_y = (SCREEN_HEIGHT - list_height) // 2

        pygame.draw.rect(surface, (40, 40, 50), (list_x, list_y, list_width, list_height), border_radius=8)
        pygame.draw.rect(surface, YELLOW, (list_x, list_y, list_width, list_height), 2, border_radius=8)

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
                pygame.draw.rect(surface, (80, 80, 100), (list_x + 5, item_y, list_width - 10, 20), border_radius=3)

            color = YELLOW if is_selected else WHITE
            text = self.font_label.render(ty.upper(), True, color)
            surface.blit(text, (list_x + 15, item_y + 2))