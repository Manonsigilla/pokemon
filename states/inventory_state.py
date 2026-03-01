import pygame
import re
import unicodedata
from states.state import State
import save_manager
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW, get_font, render_fitted_text
from models.item import ITEMS_DATABASE


class InventoryState(State):
    """Ecran d'inventaire avec visuel style Pokedex."""

    POKEDEX_RED = (220, 50, 50)
    POKEDEX_DARK = (35, 35, 40)

    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.inventory = []
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
            self._font_info = get_font(18)
        return self._font_info

    def _normalize_item_key(self, name: str) -> str:
        s = name.strip().lower()
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = re.sub(r"[\s\-]+", "_", s)
        s = re.sub(r"[^a-z0-9_]", "", s)
        return s

    def enter(self):
        print("Entré dans InventoryState")
        save_data = save_manager.load_game()
        self.inventory = []
        if save_data:
            defeated = save_data.get("defeated_entities", [])
            
            for entity_name in defeated:
                key = self._normalize_item_key(entity_name)
                # Check if it was an item
                if key in ITEMS_DATABASE:
                    item_obj = ITEMS_DATABASE[key]
                    self.inventory.append(item_obj)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN or event.key == pygame.K_m:
                    self.state_manager.change_state("map")

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill(self.POKEDEX_DARK)
        
        # Bandeau rouge en haut
        pygame.draw.rect(screen, self.POKEDEX_RED, (0, 0, SCREEN_WIDTH, 70))
        pygame.draw.rect(screen, (180, 40, 40), (0, 65, SCREEN_WIDTH, 5))
        
        title_text = "VOTRE SAC"
        title_shadow = render_fitted_text(title_text, SCREEN_WIDTH - 20, 28, (0, 0, 0), min_size=12)
        title = render_fitted_text(title_text, SCREEN_WIDTH - 20, 28, YELLOW, min_size=12)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        screen.blit(title_shadow, (title_x + 2, 22))
        screen.blit(title, (title_x, 20))
        
        start_y = 100
        if not self.inventory:
            msg = self.font_info.render("Votre sac est vide.", True, WHITE)
            screen.blit(msg, ((SCREEN_WIDTH - msg.get_width()) // 2, SCREEN_HEIGHT // 2))
        else:
            panel_width = SCREEN_WIDTH - 100
            panel_x = 50
            for i, item in enumerate(self.inventory):
                y = start_y + i * 80
                
                # Draw Item Box
                box_rect = pygame.Rect(panel_x, y, panel_width, 60)
                pygame.draw.rect(screen, (50, 50, 55), box_rect, border_radius=8)
                pygame.draw.rect(screen, (100, 100, 100), box_rect, 2, border_radius=8)
                
                # Item Name
                name_surf = render_fitted_text(item.name, panel_width - 20, 20, YELLOW, min_size=12)
                screen.blit(name_surf, (panel_x + 15, y + 10))
                
                # Item Description
                desc_surf = render_fitted_text(item.description, panel_width - 20, 16, WHITE, min_size=10)
                screen.blit(desc_surf, (panel_x + 15, y + 35))

        # Instructions
        info_bar = pygame.Surface((SCREEN_WIDTH, 40), pygame.SRCALPHA)
        info_bar.fill((0, 0, 0, 180))
        screen.blit(info_bar, (0, SCREEN_HEIGHT - 40))
        
        hint = render_fitted_text("ECHAP ou M pour revenir", SCREEN_WIDTH - 20, 18, WHITE, min_size=10)
        screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, SCREEN_HEIGHT - 30))
