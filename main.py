"""Pokemon Battle Arena - Point d'entree du jeu (Branche Manon + Gameplay Louis)."""

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE  
from api.client import APIClient
from models.type_chart import TypeChart
from models.combat import Combat
from states.state_manager import StateManager
from states.title_state import TitleState
from states.selection_state import SelectionState
from states.battle.battle_state import BattleState
from states.result_state import ResultState
from states.starter_selection_state import StarterSelectionState
from states.map_state import MapState 
from states.add_pokemon_state import AddPokemonState
from states.pokedex_state import PokedexState
from states.inventory_state import InventoryState
from states.evolution_state import EvolutionState  

class Game:
    """Classe principale du jeu. Initialise Pygame, gere la boucle de jeu."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # Services partages
        self.api_client = APIClient()
        self.type_chart = TypeChart()
        self.combat = Combat(self.type_chart)

        # State machine
        self.state_manager = StateManager()
        self.state_manager.register_state("title", TitleState(self.state_manager))
        self.state_manager.register_state("selection", SelectionState(self.state_manager, self.api_client))
        self.state_manager.register_state("battle", BattleState(self.state_manager, self.type_chart))
        self.state_manager.register_state("result", ResultState(self.state_manager))
        self.state_manager.register_state("evolution", EvolutionState(self.state_manager))
        self.state_manager.register_state("starter_selection", StarterSelectionState(self.state_manager))
        self.state_manager.register_state("map", MapState(self.state_manager))
        self.state_manager.register_state("pokedex", PokedexState(self.state_manager))
        self.state_manager.register_state("inventory", InventoryState(self.state_manager))
        self.state_manager.change_state("title")
        self.state_manager.register_state("add_pokemon", AddPokemonState(self.state_manager))
        self.state_manager.register_state("pokedex", PokedexState(self.state_manager))

    def run(self):
        """Boucle principale du jeu."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            self.state_manager.handle_events(events)
            self.state_manager.update(dt)
            self.state_manager.draw(self.screen)

            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()