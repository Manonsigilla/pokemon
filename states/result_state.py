"""Ecran de resultat du combat."""

import pygame

from states.state import State
from ui.sprite_loader import SpriteLoader
from ui.sound_manager import sound_manager
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, WHITE,
                    BG_DARK, YELLOW, GREEN, get_font, render_fitted_text)


class ResultState(State):
    """Affiche le resultat du combat avec le Pokemon gagnant."""

    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.sprite_loader = SpriteLoader()
        self.winner = None
        self.winner_sprite = None
        self._font_title = None
        self._font_info = None

    @property
    def font_title(self):
        if self._font_title is None:
            self._font_title = get_font(28)
        return self._font_title

    @property
    def font_info(self):
        if self._font_info is None:
            self._font_info = get_font(14)
        return self._font_info

    def enter(self):
        """Recupere le gagnant depuis les donnees partagees."""
        sound_manager.play_victory()
        self.winner = self.state_manager.shared_data.get("winner")

        # Gestion de la victoire en mode aventure pour supprimer l'entite de la carte
        winner_player = self.state_manager.shared_data.get("winner_player")
        player1 = self.state_manager.shared_data.get("player1")
        target_name = self.state_manager.shared_data.pop("current_encounter_name", None)
        loser_player = self.state_manager.shared_data.get("loser_player")

        self.is_adventure = self.state_manager.shared_data.get("adventure_return", False)
        self.captured = False

        if target_name and winner_player and player1 and winner_player == player1:
            self.state_manager.shared_data["victorious_over"] = target_name
            # Capturer le pokemon sauvage
            if loser_player and loser_player.name == "Pokémon Sauvage" and len(loser_player.team) > 0:
                caught_pokemon = loser_player.team[0]
                player1.add_pokemon(caught_pokemon)
                self.captured = True

        # ============ EVOLUTION ============
        # Verifier si des Pokemon du gagnant peuvent evoluer
    def enter(self):
        """Recupere le gagnant depuis les donnees partagees."""
        sound_manager.play_victory()
        self.winner = self.state_manager.shared_data.get("winner")

        # Gestion de la victoire en mode aventure
        winner_player = self.state_manager.shared_data.get("winner_player")
        player1 = self.state_manager.shared_data.get("player1")
        target_name = self.state_manager.shared_data.pop("current_encounter_name", None)
        loser_player = self.state_manager.shared_data.get("loser_player")

        self.is_adventure = self.state_manager.shared_data.get("adventure_return", False)
        self.captured = False

        if target_name and winner_player and player1 and winner_player == player1:
            self.state_manager.shared_data["victorious_over"] = target_name
            if loser_player and loser_player.name == "Pokémon Sauvage" and len(loser_player.team) > 0:
                caught_pokemon = loser_player.team[0]
                player1.add_pokemon(caught_pokemon)
                self.captured = True

        # Charger le sprite du gagnant
        if self.winner:
            try:
                self.winner_sprite = self.sprite_loader.load_sprite(
                    self.winner.front_sprite_path, scale=4
                )
            except Exception:
                self.winner_sprite = None

    def handle_events(self, events):
        """Entree pour rejouer, Echap pour quitter."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Si on revient d'un combat en mode aventure, retourner a la carte
                    if self.state_manager.shared_data.pop("adventure_return", False):
                        self.state_manager.change_state("map")
                    else:
                        self.state_manager.change_state("title")
                elif event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self, dt):
        pass

    def draw(self, surface):
        """Dessine l'ecran de victoire."""
        surface.fill(BG_DARK)

        if not self.winner:
            return

        # Titre "VICTOIRE !"
        title = self.font_title.render("VICTOIRE !", True, YELLOW)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        surface.blit(title, (title_x, 50))

        # Sprite du gagnant (apres evolution si applicable)
        if self.winner_sprite:
            sprite_x = (SCREEN_WIDTH - self.winner_sprite.get_width()) // 2
            sprite_y = 120
            surface.blit(self.winner_sprite, (sprite_x, sprite_y))

        # Nom du gagnant — adapte a la largeur de l'ecran
        winner_str = f"{self.winner.name} remporte le combat !"
        name_text = render_fitted_text(
            winner_str, SCREEN_WIDTH - 20, 18, GREEN, min_size=12
        )
        name_x = (SCREEN_WIDTH - name_text.get_width()) // 2
        surface.blit(name_text, (name_x, 430))

        # PV restants — adapte aussi
        hp_str = f"PV restants : {self.winner.current_hp}/{self.winner.max_hp}"
        hp_text = render_fitted_text(hp_str, SCREEN_WIDTH - 40, 14, WHITE, min_size=10)
        hp_x = (SCREEN_WIDTH - hp_text.get_width()) // 2
        surface.blit(hp_text, (hp_x, 465))

        # Pokemon capture
        next_y = 495
        if getattr(self, "captured", False):
            cap_str = "Pokemon ajoute au Pokedex et a l'equipe !"
            cap_text = self.font_info.render(cap_str, True, GREEN)
            cap_x = (SCREEN_WIDTH - cap_text.get_width()) // 2
            surface.blit(cap_text, (cap_x, next_y))
            next_y += 25


        # Instructions
        hint_y = max(next_y + 10, 540)
        action_text = "Entree = Continuer" if getattr(self, "is_adventure", False) else "Entree = Rejouer"
        hint1 = self.font_info.render(action_text, True, (180, 180, 180))
        hint2 = self.font_info.render("Echap = Quitter", True, (180, 180, 180))
        surface.blit(hint1, ((SCREEN_WIDTH - hint1.get_width()) // 2, hint_y))
        surface.blit(hint2, ((SCREEN_WIDTH - hint2.get_width()) // 2, hint_y + 25))