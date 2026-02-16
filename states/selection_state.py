"""Ecran de selection des Pokemon - Style Pokedex avec selection multi-Pokemon."""

import threading
import random
import pygame

from states.state import State
from models.player import Player
from ui.pokemon_card import PokemonCard
from ui.sprite_loader import SpriteLoader
from ui.sound_manager import sound_manager
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BG_DARK,
                    YELLOW, AVAILABLE_POKEMON_IDS)
from config import GAME_FONT


MAX_TEAM_SIZE = 6  # Nombre max de Pokemon par equipe


class SelectionState(State):
    """Ecran ou chaque joueur choisit son equipe - Design Pokedex."""

    POKEDEX_RED = (220, 50, 50)
    POKEDEX_DARK = (35, 35, 40)

    def __init__(self, state_manager, api_client):
        super().__init__(state_manager)
        self.api_client = api_client
        self.sprite_loader = SpriteLoader()
        self.cards = []
        self.current_player = 1
        # Changement Manon : listes d'IDs au lieu d'un seul ID
        self.selected = {1: [], 2: []}
        self.loading = True
        self.loading_progress = 0
        self.loading_total = len(AVAILABLE_POKEMON_IDS)
        self.pokemon_previews = []
        self.scroll_offset = 0
        self.max_scroll = 0
        self._font_title = None
        self._font_info = None
        self._font_loading = None
        self._font_counter = None

    @property
    def font_title(self):
        if self._font_title is None:
            self._font_title = pygame.font.Font(GAME_FONT, 25)
        return self._font_title

    @property
    def font_info(self):
        if self._font_info is None:
            self._font_info = pygame.font.Font(GAME_FONT, 20)
        return self._font_info

    @property
    def font_loading(self):
        if self._font_loading is None:
            self._font_loading = pygame.font.Font(GAME_FONT, 29)
        return self._font_loading

    @property
    def font_counter(self):
        if self._font_counter is None:
            self._font_counter = pygame.font.Font(None, 28)
        return self._font_counter

    def enter(self):
        """Lance le chargement des Pokemon."""
        self.current_player = 1
        self.selected = {1: [], 2: []}
        self.loading = True
        self.loading_progress = 0
        self.pokemon_previews = []
        self.cards = []
        self.scroll_offset = 0

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

        self._build_cards()
        self.loading = False

    def _build_cards(self):
        """Construit les PokemonCard a partir des previews."""
        self.cards = []
        cols = 5
        card_width = 140
        card_height = 170
        margin = 12
        start_x = (SCREEN_WIDTH - (cols * (card_width + margin) - margin)) // 2
        start_y = 90

        for i, preview in enumerate(self.pokemon_previews):
            col = i % cols
            row = i // cols
            x = start_x + col * (card_width + margin)
            y = start_y + row * (card_height + margin)

            try:
                sprite = self.sprite_loader.load_sprite_small(preview["sprite_path"])
            except Exception:
                sprite = None

            # Angie : Passer les stats a la carte pour l'affichage au dos (flip)
            card = PokemonCard(
                x, y, card_width, card_height,
                preview["id"], preview["name"],
                preview["types"], sprite,
                preview.get("stats", {})  # <- Les stats pour le flip !
            )
            self.cards.append(card)

        if self.cards:
            last_card = self.cards[-1]
            self.max_scroll = max(0, last_card.rect.bottom - SCREEN_HEIGHT + 50)

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

            if event.type == pygame.MOUSEWHEEL:
                self.scroll_offset -= event.y * 35
                self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state_manager.change_state("title")
                elif event.key == pygame.K_RETURN:
                    # Manon : Valider l'equipe avec Entree
                    self._confirm_team()

    def _select_pokemon(self, pokemon_id):
        """Manon : Ajoute ou retire un Pokemon de l'equipe du joueur courant."""
        current_list = self.selected[self.current_player]

        # Si deja selectionne par ce joueur, le deselectionner
        if pokemon_id in current_list:
            current_list.remove(pokemon_id)
            sound_manager.play_select()
            for card in self.cards:
                if card.pokemon_id == pokemon_id:
                    card.is_selected = False
            return

        # Verifier la limite de 6
        if len(current_list) >= MAX_TEAM_SIZE:
            return

        sound_manager.play_select()
        current_list.append(pokemon_id)
        for card in self.cards:
            if card.pokemon_id == pokemon_id:
                card.is_selected = True

    def _confirm_team(self):
        """Manon : Valide l'equipe actuelle et passe a la suite."""
        current_list = self.selected[self.current_player]

        # Il faut au moins 1 Pokemon
        if len(current_list) == 0:
            return

        sound_manager.play_select()

        mode = self.state_manager.shared_data.get("mode", "pvp")

        if self.current_player == 1:
            if mode == "pvia":
                # L'IA choisit une equipe aleatoire de meme taille
                ai_team_size = len(current_list)
                available = [pid for pid in AVAILABLE_POKEMON_IDS
                            if pid not in current_list]
                ai_team = random.sample(available, min(ai_team_size, len(available)))
                self.selected[2] = ai_team
                for card in self.cards:
                    if card.pokemon_id in ai_team:
                        card.is_selected = True
                self._start_battle()
            else:
                # Deselectionner visuellement pour le joueur 2
                for card in self.cards:
                    if card.pokemon_id not in self.selected[1]:
                        card.is_selected = False
                self.current_player = 2
        else:
            self._start_battle()

    def _start_battle(self):
        """Manon : Construit les Players avec leurs equipes et lance le combat."""
        self.loading = True

        def build_and_start():
            try:
                mode = self.state_manager.shared_data.get("mode", "pvp")

                # Construire le Player 1
                player1 = Player("Joueur 1")
                for pid in self.selected[1]:
                    pokemon = self.api_client.build_pokemon(pid)
                    player1.add_pokemon(pokemon)

                # Construire le Player 2
                if mode == "pvia":
                    difficulty = self.state_manager.shared_data.get("ai_difficulty", "normal")
                    ai_names = {
                        "facile": "Debutant",
                        "normal": "Champion",
                        "difficile": "Maitre",
                    }
                    ai_name = ai_names.get(difficulty, "Champion")
                    player2 = Player(ai_name, is_ai=True)
                else:
                    player2 = Player("Joueur 2")
                for pid in self.selected[2]:
                    pokemon = self.api_client.build_pokemon(pid)
                    player2.add_pokemon(pokemon)

                # Passer les Players via shared_data
                self.state_manager.shared_data["player1"] = player1
                self.state_manager.shared_data["player2"] = player2
                self.state_manager.shared_data["start_battle"] = True
            except Exception as e:
                print(f"Erreur construction equipe: {e}")
                import traceback
                traceback.print_exc()
                self.loading = False

        thread = threading.Thread(target=build_and_start, daemon=True)
        thread.start()

    def update(self, dt):
        """Met a jour les animations des cartes."""
        if self.state_manager.shared_data.get("start_battle"):
            self.state_manager.shared_data["start_battle"] = False
            self.state_manager.change_state("battle")

        # Angie : Mettre a jour l'animation flip de chaque carte
        for card in self.cards:
            card.update(dt)

    def draw(self, surface):
        """Dessine l'ecran de selection style Pokedex (Angie)."""
        surface.fill(self.POKEDEX_DARK)

        # Bandeau rouge (Angie)
        pygame.draw.rect(surface, self.POKEDEX_RED, (0, 0, SCREEN_WIDTH, 70))
        pygame.draw.rect(surface, (180, 40, 40), (0, 65, SCREEN_WIDTH, 5))

        if self.loading:
            self._draw_loading(surface)
            return

        # Titre avec compteur (Manon : compteur equipe)
        current_list = self.selected[self.current_player]
        count = len(current_list)

        if self.current_player == 1:
            title_text = f"Joueur 1 - Choisissez votre equipe ! ({count}/{MAX_TEAM_SIZE})"
        else:
            title_text = f"Joueur 2 - Choisissez votre equipe ! ({count}/{MAX_TEAM_SIZE})"

        # Angie : ombre sur le titre
        title_shadow = self.font_title.render(title_text, True, (0, 0, 0))
        title = self.font_title.render(title_text, True, YELLOW)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        surface.blit(title_shadow, (title_x + 2, 22))
        surface.blit(title, (title_x, 20))

        # Cartes Pokemon (avec scroll)
        for card in self.cards:
            draw_rect = card.rect.copy()
            draw_rect.y -= self.scroll_offset

            if draw_rect.bottom > 70 and draw_rect.top < SCREEN_HEIGHT - 40:
                original_rect = card.rect
                card.rect = draw_rect
                card.draw(surface)
                card.rect = original_rect

        # Barre d'instructions (Angie : semi-transparente)
        info_bar = pygame.Surface((SCREEN_WIDTH, 40), pygame.SRCALPHA)
        info_bar.fill((0, 0, 0, 180))
        surface.blit(info_bar, (0, SCREEN_HEIGHT - 40))

        # Manon : instructions adaptees au mode multi-Pokemon
        if count > 0:
            hint_text = f"Cliquez pour ajouter/retirer | Entree = Valider ({count} Pokemon) | Echap = retour"
        else:
            hint_text = "Cliquez pour selectionner | Survolez pour les stats | Echap = retour"

        hint = self.font_info.render(hint_text, True, WHITE)
        hint_x = (SCREEN_WIDTH - hint.get_width()) // 2
        surface.blit(hint, (hint_x, SCREEN_HEIGHT - 32))

        # Scrollbar (Angie)
        if self.max_scroll > 0:
            scroll_percent = self.scroll_offset / self.max_scroll
            scrollbar_height = 80
            scrollbar_y = 75 + int((SCREEN_HEIGHT - 130 - scrollbar_height) * scroll_percent)
            pygame.draw.rect(surface, (80, 80, 80), (SCREEN_WIDTH - 12, 75, 8, SCREEN_HEIGHT - 130), border_radius=4)
            pygame.draw.rect(surface, YELLOW, (SCREEN_WIDTH - 12, scrollbar_y, 8, scrollbar_height), border_radius=4)

    def _draw_loading(self, surface):
        """Dessine l'ecran de chargement (Angie : style Pokedex)."""
        text = self.font_loading.render("Chargement des Pokemon...", True, WHITE)
        text_x = (SCREEN_WIDTH - text.get_width()) // 2
        surface.blit(text, (text_x, SCREEN_HEIGHT // 2 - 40))

        bar_width = 400
        bar_height = 24
        bar_x = (SCREEN_WIDTH - bar_width) // 2
        bar_y = SCREEN_HEIGHT // 2 + 10

        # Fond arrondi
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height), border_radius=12)

        # Remplissage rouge Pokedex
        if self.loading_total > 0:
            fill = int(bar_width * self.loading_progress / self.loading_total)
            pygame.draw.rect(surface, self.POKEDEX_RED, (bar_x, bar_y, fill, bar_height), border_radius=12)

        # Bordure
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 2, border_radius=12)

        # Texte progression
        progress_text = self.font_info.render(
            f"{self.loading_progress}/{self.loading_total}", True, WHITE
        )
        progress_x = (SCREEN_WIDTH - progress_text.get_width()) // 2
        surface.blit(progress_text, (progress_x, bar_y + 35))