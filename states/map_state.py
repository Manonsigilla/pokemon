import pygame
import pytmx
import random
import json
import os
from pytmx.util_pygame import load_pygame
from states.state import State
import save_manager
from config import BASE_DIR

TILE_SIZE = 16
ENCOUNTER_CHANCE = 0.20  # 20% de chance de rencontre a chaque pas

class MapState(State):
    def __init__(self, state_manager, map_file="assets/maps/route01.tmx"):
        super().__init__(state_manager)
        self.map_file = map_file
        self.tmx_data = None
        self.player_pos = [1, 1]  # Position du joueur en tiles
        self.player_sprite = None
        self.can_move = True
        self.all_pokemon = []  # Cache des donnees pokemon pour rencontres
        
    def enter(self):
        print("Entré dans MapState")
        self.tmx_data = load_pygame(self.map_file)
        self.width = self.tmx_data.width
        self.height = self.tmx_data.height
        
        # Récupère l'index du calque Collision
        self.collision_layer_index = None
        for i, layer in enumerate(self.tmx_data.layers):
            if layer.name == "Collision":
                self.collision_layer_index = i
                break

        # Restaurer la position sauvegardee si disponible
        saved_pos = self.state_manager.shared_data.pop("saved_player_pos", None)
        if saved_pos:
            self.player_pos = list(saved_pos)
        else:
            start_obj = next((o for o in self.tmx_data.objects if o.name == "StartPosition"), None)
            self.player_pos = [int(start_obj.x // TILE_SIZE), int(start_obj.y // TILE_SIZE)] if start_obj else [1, 1]
        
        self.player_sprite = pygame.image.load("assets/sprites/player.png")
        
        from config import SCREEN_WIDTH, SCREEN_HEIGHT
        map_pixel_w = self.width * TILE_SIZE
        map_pixel_h = self.height * TILE_SIZE
        self.offset_x = (SCREEN_WIDTH - map_pixel_w) // 2
        self.offset_y = (SCREEN_HEIGHT - map_pixel_h) // 2

        # Charger les donnees pokemon pour les rencontres sauvages
        if not self.all_pokemon:
            pokemon_file = os.path.join(BASE_DIR, "bdd", "pokemon.json")
            if os.path.exists(pokemon_file):
                with open(pokemon_file, "r", encoding="utf-8") as f:
                    self.all_pokemon = json.load(f)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and self.can_move:
                dx, dy = 0, 0
                if event.key == pygame.K_UP:
                    dy = -1
                elif event.key == pygame.K_DOWN:
                    dy = 1
                elif event.key == pygame.K_LEFT:
                    dx = -1
                elif event.key == pygame.K_RIGHT:
                    dx = 1
                if dx or dy:
                    self.try_move(dx, dy)
                    
    def update (self, dt):
        pass

    def try_move(self, dx, dy):
        x, y = self.player_pos
        nx, ny = x + dx, y + dy
        if self.is_walkable(nx, ny):
            self.player_pos = [nx, ny]
            self._save_position()
            self.check_special(nx, ny)
            # Rencontre aleatoire
            self._check_wild_encounter()

    def is_walkable(self, x, y):
        if self.collision_layer_index is None:
            return True
        # Vérifie les limites de la map
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return False
        gid = self.tmx_data.get_tile_gid(x, y, self.collision_layer_index)
        return gid == 0

    def check_special(self, x, y):
        # Vérifie objets/dresseurs/baies... à la position du joueur
        for obj in self.tmx_data.objects:
            tx, ty = int(obj.x // TILE_SIZE), int(obj.y // TILE_SIZE)
            if tx == x and ty == y:
                print(f"Rencontre objet : {obj.name}")
    
    def _save_position(self):
        """Sauvegarde la position du joueur dans savegame.json."""
        save_data = save_manager.load_game()
        if save_data:
            save_manager.save_game(
                starter_id=save_data["starter_id"],
                starter_name=save_data["starter_name"],
                player_pos=self.player_pos
            )

    def _check_wild_encounter(self):
        """Verifie si une rencontre sauvage se declenche."""
        if not self.all_pokemon:
            return
        if random.random() > ENCOUNTER_CHANCE:
            return

        # Choisir un pokemon sauvage aleatoire
        wild_data = random.choice(self.all_pokemon)
        wild_level = random.randint(3, 8)

        print(f"[MapState] Rencontre sauvage : {wild_data['name']} Niv.{wild_level}")

        # Reutiliser StarterSelectionState pour creer le pokemon
        starter_state = self.state_manager.states.get("starter_selection")
        if not starter_state:
            return
        
        wild_pokemon = starter_state._create_pokemon_from_data(wild_data, level=wild_level)

        # Creer un Player IA pour le pokemon sauvage
        from models.player import Player
        wild_player = Player(name="Pokemon Sauvage", is_ai=True)
        wild_player.add_pokemon(wild_pokemon)

        # Recuperer le joueur
        player = self.state_manager.shared_data.get("player")
        if not player:
            return

        # Soigner l'equipe du joueur avant le combat
        player.heal_all()

        # Configurer le combat
        self.state_manager.shared_data["player1"] = player
        self.state_manager.shared_data["player2"] = wild_player
        self.state_manager.shared_data["mode"] = "pvia"
        self.state_manager.shared_data["ai_difficulty"] = "facile"
        self.state_manager.shared_data["adventure_return"] = True
        self.state_manager.shared_data["saved_player_pos"] = list(self.player_pos)

        self.state_manager.change_state("battle")

    def draw(self, screen):   
        screen.fill((0, 0, 0))  # Fond noir 
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledImageLayer):
                if layer.image:
                    screen.blit(layer.image, (self.offset_x, self.offset_y))
                
            elif isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    if gid != 0:
                        tile = self.tmx_data.get_tile_image_by_gid(gid)
                        if tile:
                            screen.blit(tile, (x*TILE_SIZE + self.offset_x, y*TILE_SIZE + self.offset_y))
        # Affiche le joueur
        px, py = self.player_pos
        screen.blit(self.player_sprite, (px*TILE_SIZE + self.offset_x, py*TILE_SIZE + self.offset_y))
        
    def exit(self):
        print("Sorti de MapState")