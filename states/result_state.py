"""Ecran de resultat du combat."""

import pygame

from states.state import State
from ui.sprite_loader import SpriteLoader
from pokemon.config import (SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE,
                    BG_DARK, YELLOW, GREEN)


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
            self._font_title = pygame.font.Font(None, 48)
        return self._font_title

    @property
    def font_info(self):
        if self._font_info is None:
            self._font_info = pygame.font.Font(None, 28)
        return self._font_info

    def enter(self):
        """Recupere le gagnant depuis les donnees partagees."""
        self.winner = self.state_manager.shared_data.get("winner")
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

        # Sprite du gagnant
        if self.winner_sprite:
            sprite_x = (SCREEN_WIDTH - self.winner_sprite.get_width()) // 2
            sprite_y = 120
            surface.blit(self.winner_sprite, (sprite_x, sprite_y))

        # Nom du gagnant
        name_text = self.font_title.render(
            f"{self.winner.name} remporte le combat !", True, GREEN
        )
        name_x = (SCREEN_WIDTH - name_text.get_width()) // 2
        surface.blit(name_text, (name_x, 430))

        # PV restants
        hp_text = self.font_info.render(
            f"PV restants : {self.winner.current_hp}/{self.winner.max_hp}",
            True, WHITE
        )
        hp_x = (SCREEN_WIDTH - hp_text.get_width()) // 2
        surface.blit(hp_text, (hp_x, 480))

        # Instructions
        hint1 = self.font_info.render("Entree = Rejouer", True, (150, 150, 150))
        hint2 = self.font_info.render("Echap = Quitter", True, (150, 150, 150))
        surface.blit(hint1, ((SCREEN_WIDTH - hint1.get_width()) // 2, 530))
        surface.blit(hint2, ((SCREEN_WIDTH - hint2.get_width()) // 2, 560))
