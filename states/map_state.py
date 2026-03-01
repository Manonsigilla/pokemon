import pygame
import pytmx
import json
import os
import unicodedata
import re
from models.item import ITEMS_DATABASE
from pytmx.util_pygame import load_pygame
from states.state import State
import save_manager
from config import BASE_DIR, SCREEN_WIDTH, SCREEN_HEIGHT, get_font
from models.player import Player

TILE_SIZE = 16

class MapState(State):
    def __init__(self, state_manager, map_file="assets/maps/route01.tmx"):
        super().__init__(state_manager)
        self.map_file = map_file
        self.tmx_data = None
        self.player_pos = [1, 1]  # Position du joueur en tiles
        self.player_sprite = None
        self.can_move = True
        self.all_pokemon = []  # Cache des donnees pokemon
        self.defeated_entities = set() # Noms des dresseurs/pokémons battus + objets ramassés

        # Listes d'entités sur la carte
        self.map_trainers = []
        self.map_pokemons = []
        self.map_items = []
        
        # Sprites
        self.trainer_sprite = None
        self.msg_timer = 0
        self.msg_text = ""
        
        # Menu Pause
        self.menu_active = False
        self.menu_options = ["Reprendre", "Voir Pokedex", "Voir Sac", "Sauvegarder & Quitter"]
        self.menu_index = 0
        
        # position / style de l'icône menu
        self.menu_icon_margin = 12
        self.menu_icon_bar_w = 22
        self.menu_icon_bar_h = 3
        self.menu_icon_bar_gap = 6
        self.menu_icon_color = (230, 230, 50)  # couleur des 3 barres
        # Indicateur hint (apparait quelques secondes au démarrage)
        self.show_menu_hint = True
        self.menu_hint_timer = 6.0  # secondes
        self.menu_hint_text = "Appuyez sur M pour ouvrir le menu"
        
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
        
        self.player_sprite = pygame.image.load("assets/sprites/player.png").convert_alpha()
        
        # Charger le sprite dresseur
        trainer_path = os.path.join(BASE_DIR, "assets", "sprites", "mimi.png")
        if os.path.exists(trainer_path):
            img = pygame.image.load(trainer_path).convert_alpha()
            # Redimensionner un peu pour tenir dans une case (ou un peu plus gros)
            self.trainer_sprite = pygame.transform.scale(img, (24, 24))
        
        map_pixel_w = self.width * TILE_SIZE
        map_pixel_h = self.height * TILE_SIZE
        self.offset_x = (SCREEN_WIDTH - map_pixel_w) // 2
        self.offset_y = (SCREEN_HEIGHT - map_pixel_h) // 2

        # Charger les donnees pokemon
        if not self.all_pokemon:
            pokemon_file = os.path.join(BASE_DIR, "bdd", "pokemon.json")
            if os.path.exists(pokemon_file):
                with open(pokemon_file, "r", encoding="utf-8") as f:
                    self.all_pokemon = json.load(f)

        # Si retour d'un combat, ajouter l'adversaire (s'il y en avait un) aux vaincus
        victorious_over = self.state_manager.shared_data.pop("victorious_over", None)
        if victorious_over:
            self.defeated_entities.add(victorious_over)

        self._parse_map_entities()

    def _parse_map_entities(self):
        self.map_trainers = []
        self.map_pokemons = []
        self.map_items = []
        
        for group in self.tmx_data.objectgroups:
            # Note: Le type/class est souvent défini au niveau du groupe entier dans Tiled
            # ou sur les objets. On va vérifier les deux.
            for obj in group:
                obj_class = obj.properties.get('class', obj.properties.get('type', group.properties.get('class', '')))
                
                # Attributs natifs si non trouvé dans properties
                if not obj_class:
                    obj_class = getattr(obj, 'class', getattr(group, 'class', '')) or getattr(obj, 'type', '')

                # Normaliser
                cls = str(obj_class).lower()
                name = str(obj.name)
                
                # Ignorer si déjà battu/ramassé
                if name in self.defeated_entities:
                    continue
                
                x_tile = int(obj.x // TILE_SIZE)
                y_tile = int(obj.y // TILE_SIZE)
                
                entity = {"name": name, "x": x_tile, "y": y_tile, "class": cls}
                
                if "dresseur" in cls:
                    self.map_trainers.append(entity)
                elif "pokemon" in cls or "sauvage" in cls:
                    self.map_pokemons.append(entity)
                elif "objet" in cls or "baie" in cls:
                    self.map_items.append(entity)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.menu_active:
                    if event.key == pygame.K_UP:
                        self.menu_index = (self.menu_index - 1) % len(self.menu_options)
                    elif event.key == pygame.K_DOWN:
                        self.menu_index = (self.menu_index + 1) % len(self.menu_options)
                    elif event.key == pygame.K_RETURN:
                        selected = self.menu_options[self.menu_index]
                        if selected == "Reprendre":
                            self.menu_active = False
                        elif selected == "Voir Pokedex":
                            self.state_manager.shared_data["saved_player_pos"] = list(self.player_pos)
                            self.state_manager.change_state("pokedex")
                        elif selected == "Voir Sac":
                            self.state_manager.shared_data["saved_player_pos"] = list(self.player_pos)
                            self.state_manager.change_state("inventory")
                        elif selected == "Sauvegarder & Quitter":
                            self._save_position()
                            self.state_manager.change_state("title")
                    elif event.key == pygame.K_ESCAPE or event.key == pygame.K_m:
                        self.menu_active = False
                    continue

                if event.key == pygame.K_ESCAPE or event.key == pygame.K_m:
                    self.menu_active = True
                    self.menu_index = 0
                    continue

                if self.can_move:
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

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Clic gauche
                if not self.menu_active:
                    # Vérifier le clic sur l'icône menu (3 barres)
                    icon_x = SCREEN_WIDTH - self.menu_icon_margin - self.menu_icon_bar_w
                    icon_y = self.menu_icon_margin
                    outline_rect = pygame.Rect(icon_x - 4, icon_y - 4, self.menu_icon_bar_w + 8, 3*self.menu_icon_bar_h + 2*self.menu_icon_bar_gap + 8)
                    if outline_rect.collidepoint(event.pos):
                        self.menu_active = True
                        self.menu_index = 0
                        continue
                    
    def update(self, dt):
        if self.msg_timer > 0:
            self.msg_timer -= dt
            
        # si on affiche le hint, diminuer le timer
        if self.menu_hint_timer > 0:
            self.menu_hint_timer -= dt
            if self.menu_hint_timer <= 0:
                self.show_menu_hint = False

    def try_move(self, dx, dy):
        x, y = self.player_pos
        nx, ny = x + dx, y + dy
        
        # 1. Verifier si on interagit avec une entite
        if self.check_special(nx, ny):
            return # Le mouvement est bloqué par l'entité (on lance le combat)

        # 2. Sinon déplacement classique
        if self.is_walkable(nx, ny):
            self.player_pos = [nx, ny]
            self._save_position()

    def is_walkable(self, x, y):
        # Vérifie entités (ne pas marcher SUR le dresseur ou le pokemon sauvage)
        for t in self.map_trainers:
            if t["x"] == x and t["y"] == y: return False
        for p in self.map_pokemons:
            if p["x"] == x and p["y"] == y: return False
            
        if self.collision_layer_index is None:
            return True
        # Vérifie les limites de la map
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return False
        gid = self.tmx_data.get_tile_gid(x, y, self.collision_layer_index)
        return gid == 0

    def check_special(self, nx, ny):
        """Si on essaye d'aller sur (nx, ny), déclencher l'entité si présente."""
        # 1. Objet (on marche dessus et on le ramasse)
        for item in list(self.map_items):
            if item["x"] == nx and item["y"] == ny:
                item_name = item["name"]
                self.show_message(f"Vous avez trouvé : {item_name} !")

                # retirer de la map et marquer comme ramassé
                self.defeated_entities.add(item_name)
                self.map_items.remove(item)

                # tenter d'ajouter au sac du joueur
                player = self.state_manager.shared_data.get("player")
                # normaliser la clé et rechercher dans DB
                key = self._normalize_item_key(item_name)
                item_obj = ITEMS_DATABASE.get(key)
                if player and hasattr(player, "bag") and item_obj:
                    player.bag.add_item(item_obj, quantity=1)
                    print(f"[MapState] Ajouté au sac : {item_obj.name}")
                else:
                    # Fallback / debug : si pas de player ou item introuvable
                    if not player:
                        print(f"[MapState] Aucun player trouvé pour ajouter l'objet {item_name}.")
                    if not item_obj:
                        print(f"[MapState] Item clé '{key}' introuvable dans ITEMS_DATABASE.")

                return False

        # 2. Pokémon Sauvage (Combat)
        for pkmn in self.map_pokemons:
            if pkmn["x"] == nx and pkmn["y"] == ny:
                self.start_wild_battle(pkmn)
                return True # Bloque le mouvement tant que le combat n'est pas gagné

        # 3. Dresseur (Combat IA)
        for trainer in self.map_trainers:
            if trainer["x"] == nx and trainer["y"] == ny:
                self.start_trainer_battle(trainer)
                return True # Bloque

        return False # Pas d'interaction

    def start_wild_battle(self, pkmn_entity):
        print(f"[MapState] Combat sauvage contre {pkmn_entity['name']}")
        wild_name = pkmn_entity["name"].lower()
        if wild_name == "ratata":
            wild_name = "rattata"
        wild_data = next((p for p in self.all_pokemon if p["name"] == wild_name), None)
        
        if not wild_data:
            print(f"Erreur : Pokemon {wild_name} introuvable dans bdd.")
            self.defeated_entities.add(pkmn_entity["name"]) # Éliminer le blocage
            self.map_pokemons.remove(pkmn_entity)
            return

        # Niveau bas pour le début (3 à 5)
        starter_state = self.state_manager.states.get("starter_selection")
        wild_pokemon = starter_state._create_pokemon_from_data(wild_data, level=4)

        wild_player = Player(name="Pokémon Sauvage", is_ai=True)
        wild_player.add_pokemon(wild_pokemon)

        self._launch_battle(wild_player, target_entity_name=pkmn_entity["name"])

    def start_trainer_battle(self, trainer_entity):
        print(f"[MapState] Combat contre le Dresseur {trainer_entity['name']}")
        trainer_name = trainer_entity["name"]
        
        # Construire une équipe adaptée (ex: 1 pokémon n.5)
        # On donne un Roucool à David et un Rattata à Mimi par exemple
        pkmn_name = "roucool" if trainer_name.lower() == "david" else "rattata"
        wild_data = next((p for p in self.all_pokemon if p["name"] == pkmn_name), None)
        
        trainer_player = Player(name=f"Dresseur {trainer_name}", is_ai=True)
        if wild_data:
            starter_state = self.state_manager.states.get("starter_selection")
            pkmn = starter_state._create_pokemon_from_data(wild_data, level=5)
            trainer_player.add_pokemon(pkmn)

        self._launch_battle(trainer_player, target_entity_name=trainer_name)

    def _launch_battle(self, opponent_player, target_entity_name):
        player = self.state_manager.shared_data.get("player")
        if not player: return
        
        player.heal_all() # Soin avant combat

        self.state_manager.shared_data["player1"] = player
        self.state_manager.shared_data["player2"] = opponent_player
        self.state_manager.shared_data["mode"] = "pvia"
        self.state_manager.shared_data["ai_difficulty"] = "facile"
        self.state_manager.shared_data["adventure_return"] = True
        self.state_manager.shared_data["saved_player_pos"] = list(self.player_pos)
        
        # On stocke le nom de l'entité. Le result_state ou l'écran nous le renverra pour qu'on la marque vaincue.
        self.state_manager.shared_data["current_encounter_name"] = target_entity_name

        self.state_manager.change_state("battle")

    def show_message(self, text):
        self.msg_text = text
        self.msg_timer = 2.0 # 2 secondes

    def _save_position(self):
        """Sauvegarde la position du joueur dans savegame.json."""
        save_data = save_manager.load_game()
        if save_data:
            save_manager.save_game(
                starter_id=save_data["starter_id"],
                starter_name=save_data["starter_name"],
                player_pos=self.player_pos,
                defeated_entities=list(self.defeated_entities)
            )

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
        
        # Dessiner Objets
        for item in self.map_items:
            rect = pygame.Rect(item["x"]*TILE_SIZE + self.offset_x, item["y"]*TILE_SIZE + self.offset_y, TILE_SIZE, TILE_SIZE)
            pygame.draw.circle(screen, (255, 255, 0), rect.center, 5) # Petit point jaune

        # Dessiner Pokémons Sauvages
        for pkmn in self.map_pokemons:
            rect = pygame.Rect(pkmn["x"]*TILE_SIZE + self.offset_x, pkmn["y"]*TILE_SIZE + self.offset_y, TILE_SIZE, TILE_SIZE)
            # Petit triangle rouge temp
            pygame.draw.polygon(screen, (200, 50, 50), [(rect.centerx, rect.top + 2), (rect.right - 2, rect.bottom - 2), (rect.left + 2, rect.bottom - 2)])

        # Dessiner Dresseurs
        for t in self.map_trainers:
            px = t["x"]*TILE_SIZE + self.offset_x - 4 # Ajuster centre
            py = t["y"]*TILE_SIZE + self.offset_y - 8
            if self.trainer_sprite:
                screen.blit(self.trainer_sprite, (px, py))
            else:
                rect = pygame.Rect(t["x"]*TILE_SIZE + self.offset_x, t["y"]*TILE_SIZE + self.offset_y, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, (0, 0, 255), rect) # Carré bleu temp

        # Affiche le joueur
        px, py = self.player_pos
        screen.blit(self.player_sprite, (px*TILE_SIZE + self.offset_x, py*TILE_SIZE + self.offset_y))
        
        # Message temporaire
        if self.msg_timer > 0:
            font = get_font(16)
            text_surf = font.render(self.msg_text, True, (255, 255, 255))
            rect = text_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
            # Fond sombre pour le texte
            bg_rect = rect.inflate(20, 10)
            pygame.draw.rect(screen, (30, 30, 30), bg_rect, border_radius=5)
            pygame.draw.rect(screen, (200, 200, 200), bg_rect, 2, border_radius=5)
            screen.blit(text_surf, rect)
            
        # --- Dessiner icône menu (3 barres) en haut à droite ---
        icon_x = SCREEN_WIDTH - self.menu_icon_margin - self.menu_icon_bar_w
        icon_y = self.menu_icon_margin
        for i in range(3):
            y = icon_y + i * (self.menu_icon_bar_h + self.menu_icon_bar_gap)
            rect = pygame.Rect(icon_x, y, self.menu_icon_bar_w, self.menu_icon_bar_h)
            pygame.draw.rect(screen, self.menu_icon_color, rect, border_radius=2)
        # petit contour pour lisibilité
        outline_rect = pygame.Rect(icon_x - 4, icon_y - 4, self.menu_icon_bar_w + 8, 3*self.menu_icon_bar_h + 2*self.menu_icon_bar_gap + 8)
        pygame.draw.rect(screen, (0,0,0,120), outline_rect, 1, border_radius=4)

        # --- Dessiner hint texte en haut gauche si demandé ---
        if self.show_menu_hint:
            hint_font = get_font(14)
            hint_surf = hint_font.render(self.menu_hint_text, True, (240,240,240))
            hint_bg = pygame.Rect(8, 8, hint_surf.get_width() + 12, hint_surf.get_height() + 8)
            pygame.draw.rect(screen, (10,10,10), hint_bg, border_radius=6)
            pygame.draw.rect(screen, (180,180,180), hint_bg, 1, border_radius=6)
            screen.blit(hint_surf, (hint_bg.x + 6, hint_bg.y + 4))

        # Menu Pause Overlay
        if self.menu_active:
            # Assombrir le fond
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            menu_w = 300
            menu_h = 240
            menu_x = (SCREEN_WIDTH - menu_w) // 2
            menu_y = (SCREEN_HEIGHT - menu_h) // 2
            
            # Boite du menu
            pygame.draw.rect(screen, (40, 40, 40), (menu_x, menu_y, menu_w, menu_h), border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), (menu_x, menu_y, menu_w, menu_h), 2, border_radius=10)
            
            font_title = get_font(24)
            title_surf = font_title.render("MENU", True, (255, 255, 255))
            screen.blit(title_surf, (menu_x + (menu_w - title_surf.get_width())//2, menu_y + 15))
            
            font_opt = get_font(18)
            start_y = menu_y + 70
            for i, option in enumerate(self.menu_options):
                color = (255, 255, 0) if i == self.menu_index else (200, 200, 200)
                opt_surf = font_opt.render(option, True, color)
                screen.blit(opt_surf, (menu_x + 50, start_y + i * 40))
                if i == self.menu_index:
                    # Petit curseur
                    pygame.draw.circle(screen, (255, 255, 0), (menu_x + 30, start_y + i * 40 + opt_surf.get_height()//2), 5)
                    
    def _normalize_item_key(self, name: str) -> str:
        """Normalise le nom venant de la map en clé lowercase underscore (baies_ameres)."""
        s = name.strip().lower()
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = re.sub(r"[\s\-]+", "_", s)
        s = re.sub(r"[^a-z0-9_]", "", s)
        return s

    def exit(self):
        print("Sorti de MapState")