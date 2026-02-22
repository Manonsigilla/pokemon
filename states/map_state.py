import pygame
import pytmx
from pytmx.util_pygame import load_pygame
from states.state import State

TILE_SIZE = 16

class MapState(State):
    def __init__(self, state_manager, map_file="assets/maps/route01.tmx"):
        super().__init__(state_manager)
        self.map_file = map_file
        self.tmx_data = None
        self.player_pos = [1, 1]  # Position du joueur en tiles
        self.player_sprite = None
        self.can_move = True
        
    def enter(self):
        print("Entré dans MapState")
        self.tmx_data = load_pygame(self.map_file)
        self.width = self.tmx_data.width
        self.height = self.tmx_data.height

        start_obj = next((o for o in self.tmx_data.objects if o.name == "StartPosition"), None)
        if start_obj:
            self.player_pos = [int(start_obj.x // TILE_SIZE), int(start_obj.y // TILE_SIZE)]
        else:
            self.player_pos = [1, 1]

        self.player_sprite = pygame.image.load("assets/sprites/player.png")

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
        pass  # Pas de logique de jeu pour l'instant

    def try_move(self, dx, dy):
        x, y = self.player_pos
        nx, ny = x + dx, y + dy
        if self.is_walkable(nx, ny):
            self.player_pos = [nx, ny]
            self.check_special(nx, ny)

    def is_walkable(self, x, y):
        # Nom du calque collision ! (majuscule identique à Tiled)
        gid = self.tmx_data.get_tile_gid(x, y, layer_name="Collision")
        return gid == 0  # Pas de mur

    def check_special(self, x, y):
        # Vérifie objets/dresseurs/baies... à la position du joueur
        for obj in self.tmx_data.objects:
            tx, ty = int(obj.x // TILE_SIZE), int(obj.y // TILE_SIZE)
            if tx == x and ty == y:
                print(f"Rencontre objet : {obj.name}")
    
    def draw(self, screen):   
        screen.fill((0, 0, 0))  # Fond noir 
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledImageLayer):
                if layer.image:
                    screen.blit(layer.image, (0, 0))
                
            elif isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    if gid != 0:
                        tile = self.tmx_data.get_tile_image_by_gid(gid)
                        if tile:
                            screen.blit(tile, (x*TILE_SIZE, y*TILE_SIZE))
        # Affiche le joueur
        px, py = self.player_pos
        screen.blit(self.player_sprite, (px*TILE_SIZE, py*TILE_SIZE))
        
    def exit(self):
        print("Sorti de MapState")