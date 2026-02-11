"""Ecran de selection des Pokemon."""

import threading
import pygame

from states.state import State
from ui.pokemon_card import PokemonCard
from ui.sprite_loader import SpriteLoader
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, BG_DARK,
                    YELLOW, AVAILABLE_POKEMON_IDS, BORDER_COLOR)


class SelectionState(State):
    """Ecran ou chaque joueur choisit son Pokemon."""

    def __init__(self, state_manager, api_client):
        super().__init__(state_manager)
        self.api_client = api_client
        self.sprite_loader = SpriteLoader()
        self.cards = []
        self.current_player = 1
        self.selected = {}  # {1: pokemon_id, 2: pokemon_id}
        self.loading = True
        self.loading_progress = 0
        self.loading_total = len(AVAILABLE_POKEMON_IDS)
        self.pokemon_previews = []
        self.scroll_offset = 0
        self._font_title = None
        self._font_info = None
        self._font_loading = None

    @property
    def font_title(self):
        if self._font_title is None:
            self._font_title = pygame.font.Font(None, 36)
        return self._font_title

    @property
    def font_info(self):
        if self._font_info is None:
            self._font_info = pygame.font.Font(None, 24)
        return self._font_info

    @property
    def font_loading(self):
        if self._font_loading is None:
            self._font_loading = pygame.font.Font(None, 32)
        return self._font_loading

    def enter(self):
        """Lance le chargement des Pokemon."""
        self.current_player = 1
        self.selected = {}
        self.loading = True
        self.loading_progress = 0
        self.pokemon_previews = []
        self.cards = []
        self.scroll_offset = 0

        # Charger en thread pour ne pas bloquer l'affichage
        thread = threading.Thread(target=self._load_pokemon_list, daemon=True)
        thread.start()

    def _load_pokemon_list(self):
        """Charge les previews de tous les Pokemon disponibles."""
        for pokemon_id in AVAILABLE_POKEMON_IDS:
            try:
                preview = self.api_client.get_pokemon_preview(pokemon_id)
                self.pokemon_previews.append(preview)
            except Exception as e:
                print(f"Erreur chargement Pokemon {pokemon_id}: {e}")
            self.loading_progress += 1

        # Creer les cartes une fois tout charge
        self._build_cards()
        self.loading = False

    def _build_cards(self):
        """Construit les PokemonCard a partir des previews."""
        self.cards = []
        cols = 5
        card_width = 140
        card_height = 160
        margin = 10
        start_x = (SCREEN_WIDTH - (cols * (card_width + margin) - margin)) // 2
        start_y = 80

        for i, preview in enumerate(self.pokemon_previews):
            col = i % cols
            row = i // cols
            x = start_x + col * (card_width + margin)
            y = start_y + row * (card_height + margin)

            # Charger le sprite en petit pour la carte
            try:
                sprite = self.sprite_loader.load_sprite_small(preview["sprite_path"])
            except Exception:
                sprite = None

            card = PokemonCard(
                x, y, card_width, card_height,
                preview["id"], preview["name"],
                preview["types"], sprite
            )
            self.cards.append(card)

    def handle_events(self, events):
        """Gere la selection par clic."""
        if self.loading:
            return

        mouse_pos = pygame.mouse.get_pos()
        adjusted_pos = (mouse_pos[0], mouse_pos[1] + self.scroll_offset)

        for card in self.cards:
            card.check_hover(adjusted_pos)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for card in self.cards:
                    if card.rect.collidepoint(adjusted_pos):
                        self._select_pokemon(card.pokemon_id)
                        break

            # Scroll
            if event.type == pygame.MOUSEWHEEL:
                self.scroll_offset -= event.y * 30
                self.scroll_offset = max(0, self.scroll_offset)

            # Echap pour revenir au menu
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state_manager.change_state("title")

    def _select_pokemon(self, pokemon_id):
        """Enregistre la selection d'un joueur."""
        # Empecher de choisir le meme Pokemon
        if 1 in self.selected and self.selected[1] == pokemon_id and self.current_player == 2:
            return

        self.selected[self.current_player] = pokemon_id

        # Marquer la carte comme selectionnee
        for card in self.cards:
            if card.pokemon_id == pokemon_id:
                card.is_selected = True

        mode = self.state_manager.shared_data.get("mode", "pvp")

        if self.current_player == 1:
            if mode == "pvia":
                # L'IA choisit aleatoirement
                import random
                available = [pid for pid in AVAILABLE_POKEMON_IDS if pid != pokemon_id]
                ai_choice = random.choice(available)
                self.selected[2] = ai_choice
                for card in self.cards:
                    if card.pokemon_id == ai_choice:
                        card.is_selected = True
                self._start_battle()
            else:
                self.current_player = 2
        else:
            self._start_battle()

    def _start_battle(self):
        """Construit les Pokemon complets et lance le combat."""
        self.loading = True

        def build_and_start():
            try:
                p1 = self.api_client.build_pokemon(self.selected[1])
                p2 = self.api_client.build_pokemon(self.selected[2])
                self.state_manager.shared_data["pokemon1"] = p1
                self.state_manager.shared_data["pokemon2"] = p2
                self.state_manager.shared_data["start_battle"] = True
            except Exception as e:
                print(f"Erreur construction Pokemon: {e}")
                self.loading = False

        thread = threading.Thread(target=build_and_start, daemon=True)
        thread.start()

    def update(self, dt):
        """Verifie si le combat est pret a demarrer."""
        if self.state_manager.shared_data.get("start_battle"):
            self.state_manager.shared_data["start_battle"] = False
            self.state_manager.change_state("battle")

    def draw(self, surface):
        """Dessine l'ecran de selection."""
        surface.fill(BG_DARK)

        if self.loading:
            self._draw_loading(surface)
            return

        # Titre
        mode = self.state_manager.shared_data.get("mode", "pvp")
        if self.current_player == 1:
            title_text = "Joueur 1 - Choisissez votre Pokemon !"
        else:
            title_text = "Joueur 2 - Choisissez votre Pokemon !"

        title = self.font_title.render(title_text, True, YELLOW)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        surface.blit(title, (title_x, 20))

        # Cartes Pokemon (avec scroll)
        for card in self.cards:
            # Ajuster la position avec le scroll
            draw_rect = card.rect.copy()
            draw_rect.y -= self.scroll_offset

            # Ne dessiner que si visible
            if draw_rect.bottom > 60 and draw_rect.top < SCREEN_HEIGHT:
                # Temporairement deplacer pour le dessin
                original_rect = card.rect
                card.rect = draw_rect
                card.draw(surface)
                card.rect = original_rect

        # Instructions
        hint = self.font_info.render(
            "Cliquez pour selectionner | Echap = retour", True, (150, 150, 150)
        )
        surface.blit(hint, (20, SCREEN_HEIGHT - 30))

    def _draw_loading(self, surface):
        """Dessine l'ecran de chargement."""
        text = self.font_loading.render("Chargement des Pokemon...", True, WHITE)
        text_x = (SCREEN_WIDTH - text.get_width()) // 2
        surface.blit(text, (text_x, SCREEN_HEIGHT // 2 - 40))

        # Barre de progression
        bar_width = 400
        bar_height = 20
        bar_x = (SCREEN_WIDTH - bar_width) // 2
        bar_y = SCREEN_HEIGHT // 2 + 10

        # Fond
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))

        # Remplissage
        if self.loading_total > 0:
            fill = int(bar_width * self.loading_progress / self.loading_total)
            pygame.draw.rect(surface, YELLOW, (bar_x, bar_y, fill, bar_height))

        # Bordure
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

        # Texte progression
        progress_text = self.font_info.render(
            f"{self.loading_progress}/{self.loading_total}", True, WHITE
        )
        progress_x = (SCREEN_WIDTH - progress_text.get_width()) // 2
        surface.blit(progress_text, (progress_x, bar_y + 30))
