"""Menu de selection d'attaques en grille 2x2."""

import pygame

from config import (BLACK, WHITE, BORDER_COLOR, MENU_BG,
                    TYPE_COLORS, DARK_GRAY, LIGHT_GRAY, get_font)


class MoveMenu:
    """Grille 2x2 pour la selection des attaques."""

    def __init__(self, x, y, width, height, moves):
        self.rect = pygame.Rect(x, y, width, height)
        self.moves = moves
        self.selected_index = 0
        self.visible = False
        self._font_name = None
        self._font_info = None

    @property
    def font_name(self):
        if self._font_name is None:
            self._font_name = get_font(12)
        return self._font_name

    @property
    def font_info(self):
        if self._font_info is None:
            self._font_info = get_font(10)
        return self._font_info

    def navigate(self, direction):
        """Deplace le curseur dans la grille 2x2."""
        col = self.selected_index % 2
        row = self.selected_index // 2

        if direction == "left" and col > 0:
            col -= 1
        elif direction == "right" and col < 1:
            col += 1
        elif direction == "up" and row > 0:
            row -= 1
        elif direction == "down" and row < 1:
            row += 1

        new_index = row * 2 + col
        if new_index < len(self.moves):
            self.selected_index = new_index

    def get_selected_move(self):
        """Retourne l'attaque selectionnee."""
        if self.selected_index < len(self.moves):
            return self.moves[self.selected_index]
        return self.moves[0]

    def draw(self, surface):
        """Dessine la grille 2x2 des attaques."""
        if not self.visible:
            return

        # Fond
        pygame.draw.rect(surface, MENU_BG, self.rect)
        pygame.draw.rect(surface, BORDER_COLOR, self.rect, 3)

        cell_width = self.rect.width // 2
        cell_height = self.rect.height // 2

        for i, move in enumerate(self.moves):
            col = i % 2
            row = i // 2

            cell_x = self.rect.x + col * cell_width
            cell_y = self.rect.y + row * cell_height
            cell_rect = pygame.Rect(cell_x, cell_y, cell_width, cell_height)

            # Fond de la cellule
            if i == self.selected_index:
                type_color = TYPE_COLORS.get(move.move_type, LIGHT_GRAY)
                highlight = tuple(min(255, c + 80) for c in type_color)
                pygame.draw.rect(surface, highlight, cell_rect)
            else:
                pygame.draw.rect(surface, MENU_BG, cell_rect)

            # Bordure de cellule
            pygame.draw.rect(surface, BORDER_COLOR, cell_rect, 1)

            # Nom de l'attaque
            name_color = BLACK if move.has_pp() else DARK_GRAY
            name_surface = self.font_name.render(move.display_name, True, name_color)
            surface.blit(name_surface, (cell_x + 8, cell_y + 8))

            # Type et PP
            type_text = move.move_type.title()
            pp_text = f"PP {move.current_pp}/{move.max_pp}"

            type_surface = self.font_info.render(type_text, True, DARK_GRAY)
            pp_surface = self.font_info.render(pp_text, True, DARK_GRAY)

            surface.blit(type_surface, (cell_x + 8, cell_y + 28))
            surface.blit(pp_surface, (cell_x + 8, cell_y + 42))