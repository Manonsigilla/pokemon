"""Menu de selection de Pokemon dans l'equipe pendant un combat."""

import pygame

from config import (BLACK, WHITE, BORDER_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT,
                    HP_GREEN, HP_YELLOW, HP_RED, TYPE_COLORS, DARK_GRAY)


class TeamMenu:
    """Ecran de selection d'un Pokemon dans l'equipe (overlay plein ecran)."""

    BG_COLOR = (30, 30, 40)
    SLOT_HEIGHT = 70
    SLOT_MARGIN = 8
    SLOT_WIDTH = 700

    def __init__(self):
        self.team = []            # Liste de Pokemon
        self.selected_index = 0
        self.visible = False
        self.current_pokemon = None  # Pokemon actuellement sur le terrain
        self.allow_cancel = True     # False quand switch force (KO)
        self._font_name = None
        self._font_info = None
        self._font_title = None

    @property
    def font_name(self):
        if self._font_name is None:
            self._font_name = pygame.font.Font(None, 28)
        return self._font_name

    @property
    def font_info(self):
        if self._font_info is None:
            self._font_info = pygame.font.Font(None, 22)
        return self._font_info

    @property
    def font_title(self):
        if self._font_title is None:
            self._font_title = pygame.font.Font(None, 36)
        return self._font_title

    def open(self, team, current_pokemon=None, allow_cancel=True):
        """Ouvre le menu avec l'equipe donnee."""
        self.team = team
        self.current_pokemon = current_pokemon
        self.allow_cancel = allow_cancel
        self.visible = True
        # Positionner le curseur sur le premier Pokemon vivant (pas l'actif)
        self.selected_index = 0
        for i, poke in enumerate(self.team):
            if not poke.is_fainted() and poke != current_pokemon:
                self.selected_index = i
                break

    def close(self):
        """Ferme le menu."""
        self.visible = False

    def navigate(self, direction):
        """Deplace le curseur."""
        if direction == "up" and self.selected_index > 0:
            self.selected_index -= 1
        elif direction == "down" and self.selected_index < len(self.team) - 1:
            self.selected_index += 1

    def get_selected_pokemon(self):
        """Retourne le Pokemon selectionne, ou None si invalide."""
        if self.selected_index < len(self.team):
            poke = self.team[self.selected_index]
            # Ne peut pas choisir un KO ou le pokemon deja actif
            if poke.is_fainted():
                return None
            if poke == self.current_pokemon:
                return None
            return poke
        return None

    def draw(self, surface):
        """Dessine l'ecran de selection d'equipe en overlay."""
        if not self.visible:
            return

        # Fond semi-transparent
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(self.BG_COLOR)
        overlay.set_alpha(240)
        surface.blit(overlay, (0, 0))

        # Titre
        if self.allow_cancel:
            title_text = "Choisissez un Pokemon"
        else:
            title_text = "Choisissez le Pokemon suivant !"
        title = self.font_title.render(title_text, True, WHITE)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        surface.blit(title, (title_x, 20))

        # Slots de l'equipe
        start_x = (SCREEN_WIDTH - self.SLOT_WIDTH) // 2
        start_y = 70

        for i, poke in enumerate(self.team):
            slot_y = start_y + i * (self.SLOT_HEIGHT + self.SLOT_MARGIN)
            slot_rect = pygame.Rect(start_x, slot_y, self.SLOT_WIDTH, self.SLOT_HEIGHT)

            # Couleur de fond du slot
            if poke.is_fainted():
                bg_color = (80, 40, 40)  # Rouge sombre = KO
            elif poke == self.current_pokemon:
                bg_color = (40, 60, 80)  # Bleu = actif sur le terrain
            elif i == self.selected_index:
                bg_color = (60, 100, 60)  # Vert = selectionne
            else:
                bg_color = (50, 50, 60)  # Gris = normal

            pygame.draw.rect(surface, bg_color, slot_rect, border_radius=8)
            pygame.draw.rect(surface, BORDER_COLOR, slot_rect, 2, border_radius=8)

            # Nom du Pokemon
            name_text = self.font_name.render(poke.name, True, WHITE)
            surface.blit(name_text, (slot_rect.x + 15, slot_rect.y + 8))

            # Niveau
            level_text = self.font_info.render(f"Nv.{poke.level}", True, (200, 200, 200))
            surface.blit(level_text, (slot_rect.x + 15, slot_rect.y + 35))

            # Types
            type_x = slot_rect.x + 100
            for t in poke.types:
                type_color = TYPE_COLORS.get(t, (150, 150, 150))
                type_label = self.font_info.render(t.title(), True, WHITE)
                tag_rect = pygame.Rect(type_x, slot_rect.y + 35, type_label.get_width() + 10, 20)
                pygame.draw.rect(surface, type_color, tag_rect, border_radius=4)
                surface.blit(type_label, (type_x + 5, slot_rect.y + 37))
                type_x += tag_rect.width + 5

            # Barre de PV
            bar_x = slot_rect.x + 350
            bar_y = slot_rect.y + 12
            bar_width = 250
            bar_height = 10

            pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_width, bar_height))
            if poke.max_hp > 0:
                fill_ratio = max(0, poke.current_hp / poke.max_hp)
                fill_width = int(bar_width * fill_ratio)
                if fill_ratio > 0.5:
                    bar_color = HP_GREEN
                elif fill_ratio > 0.2:
                    bar_color = HP_YELLOW
                else:
                    bar_color = HP_RED
                if fill_width > 0:
                    pygame.draw.rect(surface, bar_color, (bar_x, bar_y, fill_width, bar_height))
            pygame.draw.rect(surface, BORDER_COLOR, (bar_x, bar_y, bar_width, bar_height), 1)

            # Texte PV
            hp_text = self.font_info.render(
                f"{poke.current_hp}/{poke.max_hp} PV", True, WHITE
            )
            surface.blit(hp_text, (bar_x, bar_y + 15))

            # Indicateurs speciaux
            if poke.is_fainted():
                ko_text = self.font_name.render("K.O.", True, (255, 80, 80))
                surface.blit(ko_text, (slot_rect.right - 70, slot_rect.y + 22))
            elif poke == self.current_pokemon:
                active_text = self.font_info.render("En combat", True, (100, 180, 255))
                surface.blit(active_text, (slot_rect.right - 100, slot_rect.y + 25))

            # Fleche de selection
            if i == self.selected_index and not poke.is_fainted() and poke != self.current_pokemon:
                arrow = self.font_name.render(">", True, (255, 255, 100))
                surface.blit(arrow, (start_x - 25, slot_rect.y + 20))

        # Instructions en bas
        if self.allow_cancel:
            hint_text = "Haut/Bas = Naviguer | Entree = Choisir | Echap = Retour"
        else:
            hint_text = "Haut/Bas = Naviguer | Entree = Choisir"
        hint = self.font_info.render(hint_text, True, (150, 150, 150))
        hint_x = (SCREEN_WIDTH - hint.get_width()) // 2
        surface.blit(hint, (hint_x, SCREEN_HEIGHT - 30))