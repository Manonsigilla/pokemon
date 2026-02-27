import pygame
from states.state import State
import save_manager
from config import SCREEN_WIDTH, SCREEN_HEIGHT, BG_DARK, WHITE, YELLOW, get_font

class InventoryState(State):
    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.font_title = get_font(28)
        self.font_info = get_font(18)
        self.inventory = []

    def enter(self):
        print("Entré dans InventoryState")
        save_data = save_manager.load_game()
        self.inventory = []
        if save_data:
            defeated = save_data.get("defeated_entities", [])
            # Les baies et objets sont capitalisés ou commencent par majuscule depuis Tiled
            # On va juste filtrer "Baies_ameres"
            for d in defeated:
                if d.lower() == "baies_ameres":
                    self.inventory.append("Baie amère")
                # On peut rajouter d'autres objets plus tard

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    self.state_manager.change_state("map")

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill(BG_DARK)
        
        title = self.font_title.render("SAC (Objets)", True, YELLOW)
        screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 40))
        
        start_y = 120
        if not self.inventory:
            msg = self.font_info.render("Votre sac est vide.", True, WHITE)
            screen.blit(msg, ((SCREEN_WIDTH - msg.get_width()) // 2, SCREEN_HEIGHT // 2))
        else:
            for i, item in enumerate(self.inventory):
                opt_surf = self.font_info.render(f"- {item}", True, WHITE)
                screen.blit(opt_surf, (80, start_y + i * 40))

        hint = self.font_info.render("ECHAP pour revenir", True, (150, 150, 150))
        screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, SCREEN_HEIGHT - 40))
