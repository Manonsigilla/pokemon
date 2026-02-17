"""Mixin de rendu pour l'ecran de combat."""

import pygame

from ui.hp_bar import HPBar
from ui.text_box import TextBox
from ui.move_menu import MoveMenu
from ui.damage_number import DamageNumber
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, WHITE,
                    PLAYER_SPRITE_POS, ENEMY_SPRITE_POS,
                    PLAYER_INFO_POS, ENEMY_INFO_POS,
                    TEXT_BOX_RECT, MOVE_TEXT_RECT, MOVE_MENU_RECT)

from states.battle.constants import PHASE_ACTION_P1, PHASE_CHOOSE_P1


class BattleRenderer:
    """Methodes de rendu de l'ecran de combat."""

    def _load_sprites(self):
        """Charge les sprites des Pokemon actifs."""
        self.player_sprite = self.sprite_loader.load_sprite(
            self.battle.pokemon1.back_sprite_path
        )
        self.enemy_sprite = self.sprite_loader.load_sprite(
            self.battle.pokemon2.front_sprite_path
        )

    def _create_ui(self):
        """Cree les widgets UI pour les Pokemon actifs."""
        self.hp_bar_p2 = HPBar(
            ENEMY_INFO_POS[0], ENEMY_INFO_POS[1],
            250, self.battle.pokemon2, show_hp_text=False
        )
        self.hp_bar_p1 = HPBar(
            PLAYER_INFO_POS[0], PLAYER_INFO_POS[1],
            250, self.battle.pokemon1, show_hp_text=True
        )
        self.text_box = TextBox(*TEXT_BOX_RECT)
        self.move_menu = MoveMenu(*MOVE_MENU_RECT, self.battle.pokemon1.moves)

    def _refresh_ui_after_switch(self, player_num):
        """Manon : Met a jour les sprites et barres de vie apres un switch."""
        from battle.ai import AIOpponent

        if player_num == 1:
            self.player_sprite = self.sprite_loader.load_sprite(
                self.battle.pokemon1.back_sprite_path
            )
            self.hp_bar_p1 = HPBar(
                PLAYER_INFO_POS[0], PLAYER_INFO_POS[1],
                250, self.battle.pokemon1, show_hp_text=True
            )
            # Angie : reset position sprite
            self.player_sprite_pos = list(PLAYER_SPRITE_POS)
        else:
            self.enemy_sprite = self.sprite_loader.load_sprite(
                self.battle.pokemon2.front_sprite_path
            )
            self.hp_bar_p2 = HPBar(
                ENEMY_INFO_POS[0], ENEMY_INFO_POS[1],
                250, self.battle.pokemon2, show_hp_text=False
            )
            # Angie : reset position sprite
            self.enemy_sprite_pos = list(ENEMY_SPRITE_POS)
            # Manon : mettre a jour l'IA
            if self.ai:
                self.ai = AIOpponent(
                    self.battle.pokemon2, self.type_chart,
                    difficulty=self.ai_difficulty,
                    team=self.battle.player2.team
                )

    def draw(self, surface):
        """Dessine l'ecran de combat complet."""
        # Louis : fond de l'arene
        self._draw_background(surface)

        # Angie : sprites aux positions animees
        if self.player_sprite:
            surface.blit(self.player_sprite, self.player_sprite_pos)
        if self.enemy_sprite:
            surface.blit(self.enemy_sprite, self.enemy_sprite_pos)

        # Barres de vie
        self.hp_bar_p1.draw(surface)
        self.hp_bar_p2.draw(surface)

        # Manon : indicateurs d'equipe (petites pokeballs)
        self._draw_team_indicators(surface)

        # Angie : particules d'impact
        for particles in self.impact_particles:
            particles.draw(surface)

        # Angie : degats flottants
        for dmg_num in self.damage_numbers:
            dmg_num.draw(surface)

        # Zone de texte / menus
        if self.action_menu and self.action_menu.visible:
            action_box = TextBox(*MOVE_TEXT_RECT)
            if self.phase == PHASE_ACTION_P1:
                action_box.set_text(f"Que doit faire {self.battle.pokemon1.name} ?")
            else:
                action_box.set_text(f"Que doit faire {self.battle.pokemon2.name} ?")
            action_box.skip_animation()
            action_box.draw(surface)
            self.action_menu.draw(surface)

            controls = "W/S + Espace" if self.phase == PHASE_ACTION_P1 else "Haut/Bas + Entree"
            ctrl_text = self.font_controls.render(controls, True, (100, 100, 100))
            surface.blit(ctrl_text, (10, SCREEN_HEIGHT - 18))

        elif self.move_menu and self.move_menu.visible:
            action_box = TextBox(*MOVE_TEXT_RECT)
            if self.phase == PHASE_CHOOSE_P1:
                action_box.set_text(f"Que doit faire {self.battle.pokemon1.name} ?")
            else:
                action_box.set_text(f"Que doit faire {self.battle.pokemon2.name} ?")
            action_box.skip_animation()
            action_box.draw(surface)
            self.move_menu.draw(surface)

            controls = "WASD + Espace | Echap = retour" if self.phase == PHASE_CHOOSE_P1 else "Fleches + Entree | Echap = retour"
            ctrl_text = self.font_controls.render(controls, True, (100, 100, 100))
            surface.blit(ctrl_text, (10, SCREEN_HEIGHT - 18))
        else:
            self.text_box.draw(surface)

        # Louis : flash d'attaque
        if self.flash_alpha > 0:
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surface.fill(WHITE)
            flash_surface.set_alpha(int(self.flash_alpha))
            surface.blit(flash_surface, (0, 0))

        # Angie : flash d'efficacite
        if self.effectiveness_flash:
            self.effectiveness_flash.draw(surface)

        # Manon : team menu en overlay (par dessus tout)
        if self.team_menu and self.team_menu.visible:
            self.team_menu.draw(surface)

    def _draw_team_indicators(self, surface):
        """Dessine des indicateurs (pokeballs) pour chaque Pokemon de l'equipe."""
        indicator_size = 12
        spacing = 18

        # Equipe J1 (sous la barre de vie du joueur, a gauche)
        start_x_p1 = 50
        y_p1 = PLAYER_SPRITE_POS[1] + 170  # Sous le sprite joueur
        for i, poke in enumerate(self.battle.player1.team):
            x = start_x_p1 + i * spacing
            if poke.is_fainted():
                color = (180, 50, 50)   # Rouge = KO
            elif poke == self.battle.pokemon1:
                color = (60, 200, 60)   # Vert = actif
            else:
                color = (220, 220, 220) # Blanc/gris = en reserve
            pygame.draw.circle(surface, color, (x, y_p1), indicator_size // 2)
            pygame.draw.circle(surface, (30, 30, 30), (x, y_p1), indicator_size // 2, 1)

        # Equipe J2 (sous la barre de vie de l'ennemi, a droite)
        start_x_p2 = ENEMY_INFO_POS[0] + 200
        y_p2 = ENEMY_INFO_POS[1] + 60  # Juste sous le panneau ennemi
        for i, poke in enumerate(self.battle.player2.team):
            x = start_x_p2 + i * spacing
            if poke.is_fainted():
                color = (180, 50, 50)   # Rouge = KO
            elif poke == self.battle.pokemon2:
                color = (60, 200, 60)   # Vert = actif
            else:
                color = (220, 220, 220) # Blanc/gris = en reserve
            pygame.draw.circle(surface, color, (x, y_p2), indicator_size // 2)
            pygame.draw.circle(surface, (30, 30, 30), (x, y_p2), indicator_size // 2, 1)

    def _draw_background(self, surface):
        """Louis : Dessine le fond de l'arene avec l'image chargee."""
        if self.background_image:
            surface.blit(self.background_image, (0, 0))
        else:
            # Fallback GBA (Manon/Angie)
            surface.fill((136, 192, 240))
            pygame.draw.ellipse(surface, (144, 200, 120), (420, 230, 320, 60))
            pygame.draw.ellipse(surface, (120, 176, 100), (420, 230, 320, 60), 2)
            pygame.draw.ellipse(surface, (144, 200, 120), (20, 420, 350, 70))
            pygame.draw.ellipse(surface, (120, 176, 100), (20, 420, 350, 70), 2)
            pygame.draw.rect(surface, (120, 176, 100), (0, 430, SCREEN_WIDTH, 170))
