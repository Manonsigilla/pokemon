"""
Ecran de selection du Pokemon starter (Bulbizarre, Salameche, Carapuce).
Le joueur commence son aventure en choisissant UN SEUL Pokemon parmi les 3 starters.
"""

import pygame
import json
import os
import urllib.request

from states.state import State  # Classe de base pour tous les etats
from models.pokemon import Pokemon  # Classe Pokemon pour creer le starter
from models.move import Move  # Classe Move pour les attaques
from models.player import Player  # Classe Player pour le dresseur
from ui.sprite_loader import SpriteLoader  # Pour charger les sprites Pokemon
from ui.sound_manager import sound_manager  # Pour la musique
from config import (
    SCREEN_WIDTH, 
    SCREEN_HEIGHT, 
    WHITE, 
    BG_DARK, 
    YELLOW, 
    GREEN,
    BASE_DIR,
    get_font,
    render_fitted_text
)


class StarterSelectionState(State):
    """
    Ecran de selection du starter.
    Le joueur choisit entre Bulbizarre (ID 1), Salameche (ID 4), Carapuce (ID 7).
    """

    def __init__(self, state_manager):
        """
        Initialise l'ecran de selection du starter.
        
        Args:
            state_manager: Le gestionnaire d'etats du jeu (pour changer d'ecran)
        """
        super().__init__(state_manager)
        
        # ============ IDs DES STARTERS ============
        # Les 3 Pokemon de depart de la Generation 1
        self.STARTER_IDS = [1, 4, 7]  # Bulbizarre, Salameche, Carapuce
        
        # ============ DONNEES DES STARTERS ============
        self.starters_data = []  # Liste des donnees JSON des 3 starters
        self.starter_cards = []  # Liste des "cartes" pour afficher chaque starter
        
        # ============ SELECTION DU JOUEUR ============
        self.selected_index = 0  # Index du starter selectionne (0, 1 ou 2)
        
        # ============ SPRITES ============
        self.sprite_loader = SpriteLoader()  # Gestionnaire de sprites
        self.starter_sprites = {}  # Dictionnaire {pokemon_id: sprite_surface}
        
        # ============ CACHE DES SPRITES TELECHARGES ============
        self.cache_dir = os.path.join(BASE_DIR, "cache", "starter_sprites")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # ============ FONTS (chargement paresseux) ============
        # On ne charge les fonts que quand on en a besoin (performance)
        self._font_title = None
        self._font_name = None
        self._font_info = None
        self._font_instruction = None
        
        # Animation du titre (pulsation)
        self.title_pulse = 0
    
    
    # ========================================
    # PROPRIETES POUR LES FONTS (LAZY LOADING)
    # ========================================
    # On utilise des "properties" pour ne charger les fonts que si necessaire
    
    @property
    def font_title(self):
        """Font pour le titre principal."""
        if self._font_title is None:
            self._font_title = get_font(28)
        return self._font_title
    
    @property
    def font_name(self):
        """Font pour les noms des Pokemon."""
        if self._font_name is None:
            self._font_name = get_font(20)  # Reduit pour eviter debordement
        return self._font_name
    
    @property
    def font_info(self):
        """Font pour les infos (types, stats)."""
        if self._font_info is None:
            self._font_info = get_font(16)  # Reduit pour eviter debordement
        return self._font_info
    
    @property
    def font_instruction(self):
        """Font pour les instructions en bas d'ecran."""
        if self._font_instruction is None:
            self._font_instruction = get_font(16)
        return self._font_instruction
    
    
    # ========================================
    # METHODES DU CYCLE DE VIE DE L'ETAT
    # ========================================
    
    def enter(self):
        """
        Appele quand on entre dans cet ecran.
        Charge les donnees des 3 starters et leurs sprites.
        """
        print("[StarterSelection] Entree dans l'ecran de selection du starter")
        
        # ============ CHARGEMENT DES DONNEES ============
        self._load_starters_data()
        
        # ============ CHARGEMENT DES SPRITES ============
        self._load_starter_sprites()
        
        # ============ CREATION DES CARTES D'AFFICHAGE ============
        self._build_starter_cards()
        
        # ============ MUSIQUE ============
        # Ne jouer la musique que si aucune musique en cours
        if not pygame.mixer.music.get_busy():
            sound_manager.play_music("pokemontheme.mp3")
        
        # Reset de la selection
        self.selected_index = 0
    
    def exit(self):
        """
        Appele quand on quitte cet ecran.
        Nettoie les ressources si necessaire.
        """
        pass  # Pas de nettoyage necessaire pour l'instant
    
    
    # ========================================
    # CHARGEMENT DES DONNEES
    # ========================================
    
    def _load_starters_data(self):
        """
        Charge les donnees des 3 starters depuis bdd/pokemon.json.
        On filtre uniquement les Pokemon avec les IDs 1, 4, 7.
        """
        # Chemin vers le fichier JSON contenant tous les Pokemon
        pokemon_file = os.path.join(BASE_DIR, "bdd", "pokemon.json")
        
        # Verification que le fichier existe
        if not os.path.exists(pokemon_file):
            print(f"[ERREUR] Fichier {pokemon_file} introuvable !")
            self.starters_data = []
            return
        
        # Chargement du fichier JSON
        with open(pokemon_file, "r", encoding="utf-8") as f:
            all_pokemon = json.load(f)
        
        # Filtrer pour ne garder que les 3 starters
        self.starters_data = [
            poke for poke in all_pokemon if poke["id"] in self.STARTER_IDS
        ]
        
        # Trier pour avoir l'ordre : Bulbizarre, Salameche, Carapuce
        self.starters_data.sort(key=lambda p: self.STARTER_IDS.index(p["id"]))
        
        print(f"[StarterSelection] {len(self.starters_data)} starters charges")
    
    
    def _download_sprite(self, url):
        """
        Telecharge un sprite depuis une URL et le sauvegarde en cache.
        
        Args:
            url (str): URL du sprite a telecharger
        
        Returns:
            str: Chemin local du sprite telecharge, ou None si echec
        """
        # Creer un nom de fichier unique base sur l'URL
        filename = url.split("/")[-1]
        filepath = os.path.join(self.cache_dir, filename)
        
        # Si deja en cache, retourner le chemin
        if os.path.exists(filepath):
            print(f"[StarterSelection] Sprite deja en cache : {filename}")
            return filepath
        
        # Telecharger le sprite
        try:
            print(f"[StarterSelection] Telechargement de {url}...")
            urllib.request.urlretrieve(url, filepath)
            print(f"[StarterSelection] Sprite telecharge : {filename}")
            return filepath
        except Exception as e:
            print(f"[ERREUR] Impossible de telecharger {url}: {e}")
            return None
    
    
    def _load_starter_sprites(self):
        """
        Charge les sprites des 3 starters.
        Telecharge les sprites depuis les URLs si necessaire.
        """
        for starter in self.starters_data:
            pokemon_id = starter["id"]
            sprite_url = starter["sprites"]["front_default"]
            
            sprite_path = self._download_sprite(sprite_url)
            
            if sprite_path and os.path.exists(sprite_path):
                try:
                    # Charger le sprite avec une echelle de 3.5 (pour qu'il soit assez gros)
                    sprite = self.sprite_loader.load_sprite(sprite_path, scale=3)
                    self.starter_sprites[pokemon_id] = sprite
                    print(f"[StarterSelection] Sprite charge pour {starter['name']}")
                except Exception as e:
                    print(f"[ERREUR] Impossible de charger le sprite de {starter['name']}: {e}")
                    # En cas d'erreur, on cree un sprite vide (rectangle gris)
                    self.starter_sprites[pokemon_id] = pygame.Surface((128, 128))
                    self.starter_sprites[pokemon_id].fill((100, 100, 100))
            else:
                # Sprite de remplacement si telechargement echoue
                print(f"[ERREUR] Sprite introuvable pour {starter['name']}, creation d'un placeholder")
                self.starter_sprites[pokemon_id] = pygame.Surface((128, 128))
                self.starter_sprites[pokemon_id].fill((100, 100, 100))
    
    
    def _build_starter_cards(self):
        """
        Construit les "cartes" d'affichage pour chaque starter.
        Chaque carte contient : position (x, y), largeur, hauteur, donnees Pokemon.
        """
        self.starter_cards = []
        
        # ============ CALCUL DES POSITIONS ============
        # On veut afficher 3 cartes cote a cote, centrees horizontalement
        card_width = 240   # Largeur augmentee
        card_height = 360  # Hauteur augmentee
        spacing = 20       # Espace entre les cartes
        
        # Position Y (verticale) : centre de l'ecran
        start_y = (SCREEN_HEIGHT - card_height) // 2 + 20
        
        # Position X (horizontale) : centre les 3 cartes
        total_width = (card_width * 3) + (spacing * 2)
        start_x = (SCREEN_WIDTH - total_width) // 2
        
        # ============ CREATION DES CARTES ============
        for i, starter in enumerate(self.starters_data):
            card = {
                "x": start_x + (i * (card_width + spacing)),  # Position X
                "y": start_y,                                  # Position Y
                "width": card_width,
                "height": card_height,
                "data": starter,  # Donnees JSON du Pokemon
                "pokemon_id": starter["id"]
            }
            self.starter_cards.append(card)
        
        print(f"[StarterSelection] {len(self.starter_cards)} cartes creees")
    
    
    # ========================================
    # GESTION DES EVENEMENTS (CLAVIER/SOURIS)
    # ========================================
    
    def handle_events(self, events):
        """
        Gere les evenements utilisateur (clavier, souris).
        
        - FLECHES GAUCHE/DROITE : changer de starter
        - ENTREE : confirmer la selection
        - SOURIS : cliquer sur une carte pour la selectionner
        
        Args:
            events: Liste des evenements Pygame
        """
        # Position actuelle de la souris
        mouse_pos = pygame.mouse.get_pos()
        
        # ============ PARCOURIR TOUS LES EVENEMENTS ============
        for event in events:
            
            # ---------- CLAVIER ----------
            if event.type == pygame.KEYDOWN:
                
                # FLECHE GAUCHE : selectionner le starter precedent
                if event.key == pygame.K_LEFT:
                    self.selected_index = (self.selected_index - 1) % len(self.starter_cards)
                    sound_manager.play_select()  # Son de selection
                
                # FLECHE DROITE : selectionner le starter suivant
                elif event.key == pygame.K_RIGHT:
                    self.selected_index = (self.selected_index + 1) % len(self.starter_cards)
                    sound_manager.play_select()  # Son de selection
                
                # ENTREE : confirmer la selection du starter
                elif event.key == pygame.K_RETURN:
                    self._confirm_selection()
            
            # ---------- SOURIS ----------
            # Si on clique avec le bouton gauche de la souris
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Verifier si on a clique sur une carte
                for i, card in enumerate(self.starter_cards):
                    # Creer un rectangle pour la carte
                    card_rect = pygame.Rect(card["x"], card["y"], card["width"], card["height"])
                    
                    # Si la souris est dans ce rectangle
                    if card_rect.collidepoint(mouse_pos):
                        self.selected_index = i  # Selectionner cette carte
                        sound_manager.play_select()  # Son de selection
    
    
    def _confirm_selection(self):
        """
        Confirme la selection du starter et passe a l'ecran suivant.
        
        Cette methode :
        1. Cree un objet Pokemon a partir des donnees JSON
        2. Cree un joueur (Player) avec ce Pokemon
        3. Stocke le joueur dans shared_data pour le passer aux autres ecrans
        4. Change d'etat (par exemple vers une map ou un combat)
        """
        print(f"[StarterSelection] Starter choisi : index {self.selected_index}")
        
        # ============ RECUPERER LES DONNEES DU STARTER ============
        selected_card = self.starter_cards[self.selected_index]
        starter_data = selected_card["data"]
        
        # ============ CREER LE POKEMON ============
        # On cree un Pokemon niveau 5 (niveau de depart classique)
        starter_pokemon = self._create_pokemon_from_data(starter_data, level=5)
        
        # ============ CREER LE JOUEUR ============
        # Le joueur humain avec son Pokemon de depart
        player = Player(name="Joueur", is_ai=False)
        player.add_pokemon(starter_pokemon)
        
        # ============ STOCKER DANS SHARED_DATA ============
        # On partage le joueur avec les autres ecrans via state_manager.shared_data
        self.state_manager.shared_data["player"] = player
        self.state_manager.shared_data["starter_selected"] = True
        
        # ============ CHANGER D'ETAT ============
        # Pour l'instant, on retourne au menu titre (tu changeras ca plus tard)
        # Remplace "title" par "map" ou "pokedex" selon ton besoin
        print(f"[StarterSelection] Changement d'etat vers 'title' (temporaire)")
        self.state_manager.change_state("title")
        
        # TODO : Remplacer par le vrai etat (map, intro, etc.)
        # self.state_manager.change_state("map")
    
    
    def _create_pokemon_from_data(self, pokemon_data, level):
        """
        Cree un objet Pokemon a partir des donnees JSON.
        
        Args:
            pokemon_data (dict): Donnees JSON du Pokemon (depuis bdd/pokemon.json)
            level (int): Niveau du Pokemon
        
        Returns:
            Pokemon: Un objet Pokemon pret a l'emploi
        """
        # ============ EXTRACTION DES DONNEES ============
        pokemon_id = pokemon_data["id"]
        name = pokemon_data["name"]
        types = pokemon_data["types"]
        base_stats = pokemon_data["stats"]
        
        # ============ CREATION DES ATTAQUES ============
        # On prend les 4 premieres attaques disponibles
        # (dans un vrai jeu, les starters niveau 5 ont peu d'attaques)
        move_names = pokemon_data["moves"][:4]  # Maximum 4 attaques
        moves = self._create_moves(move_names, types)
        
        # ============ TELECHARGEMENT DES SPRITES ============
        # Telecharger les sprites front et back
        front_sprite_url = pokemon_data["sprites"]["front_default"]
        back_sprite_url = pokemon_data["sprites"]["back_default"]
        
        front_sprite_path = self._download_sprite(front_sprite_url)
        back_sprite_path = self._download_sprite(back_sprite_url)
        
        # ============ CREATION DU POKEMON ============
        pokemon = Pokemon(
            pokemon_id=pokemon_id,
            name=name,
            level=level,
            types=types,
            base_stats=base_stats,
            moves=moves,
            front_sprite_path=front_sprite_path,
            back_sprite_path=back_sprite_path
        )
        
        print(f"[StarterSelection] Pokemon cree : {pokemon.name} Niv.{level}")
        return pokemon
    
    
    def _create_moves(self, move_names, pokemon_types):
        """
        Cree une liste d'objets Move a partir de noms d'attaques.
        
        NOTE : Pour l'instant, on cree des attaques simplifiees.
        Dans un vrai jeu, tu chargerais les vraies donnees depuis l'API.
        
        Args:
            move_names (list): Liste de noms d'attaques (ex: ["tackle", "growl"])
            pokemon_types (list): Types du Pokemon (pour assigner un type aux attaques)
        
        Returns:
            list: Liste d'objets Move
        """
        moves = []
        
        for move_name in move_names:
            # ============ ATTAQUES SIMPLIFIEES ============
            # Pour l'instant, on donne des valeurs par defaut
            # Plus tard, tu pourras charger les vraies stats depuis l'API
            
            # Valeurs par defaut
            power = 40
            accuracy = 100
            pp = 25
            move_type = pokemon_types[0] if pokemon_types else "normal"  # Type principal
            category = "physical"
            
            # Creer l'attaque
            move = Move(
                name=move_name,
                power=power,
                accuracy=accuracy,
                pp=pp,
                move_type=move_type,
                category=category
            )
            
            moves.append(move)
        
        # Assurer au moins 1 attaque
        if not moves:
            moves.append(Move("tackle", 40, 100, 35, "normal", "physical"))
        
        return moves
    
    
    # ========================================
    # MISE A JOUR (BOUCLE DE JEU)
    # ========================================
    
    def update(self, dt):
        """Animation de pulsation du titre."""
        import math
        self.title_pulse += dt * 3  # Vitesse de pulsation
        if self.title_pulse > 2 * math.pi:
            self.title_pulse -= 2 * math.pi
    
    
    # ========================================
    # AFFICHAGE (RENDU GRAPHIQUE)
    # ========================================
    
    def draw(self, surface):
        """Affichage avec degrade et animations."""
        # Fond avec degrade vertical (sombre en haut, plus clair en bas)
        self._draw_gradient_background(surface)
        
        # Titre avec effet de pulsation
        self._draw_animated_title(surface)
        
        # Cartes des starters
        for i, card in enumerate(self.starter_cards):
            is_selected = (i == self.selected_index)
            self._draw_starter_card(surface, card, is_selected)
        
        # Instructions avec fond semi-transparent
        self._draw_instructions(surface)
        
    def _draw_gradient_background(self, surface):
        """Degrade vertical du noir vers gris fonce."""
        for y in range(SCREEN_HEIGHT):
            # Interpolation de couleur
            ratio = y / SCREEN_HEIGHT
            color_value = int(40 + (ratio * 30))  # De 40 a 70
            color = (color_value, color_value, color_value)
            pygame.draw.line(surface, color, (0, y), (SCREEN_WIDTH, y))
    
    def _draw_animated_title(self, surface):
        """Titre avec effet de pulsation — adapte a la largeur de l'ecran."""
        import math
        
        # Calculer l'offset de pulsation
        pulse_offset = int(math.sin(self.title_pulse) * 2)
        
        title_str = "Choisis ton Pokemon de depart !"
        max_width = SCREEN_WIDTH - 40  # 20px marge de chaque cote
        
        # Ombre portee — adaptee
        shadow_text = render_fitted_text(title_str, max_width, 28, (30, 30, 30), min_size=14)
        # Titre — adapte
        title_text = render_fitted_text(title_str, max_width, 28, YELLOW, min_size=14)
        
        title_x = (SCREEN_WIDTH - title_text.get_width()) // 2
        title_y = 25 + pulse_offset
        
        surface.blit(shadow_text, (title_x + 3, title_y + 3))
        surface.blit(title_text, (title_x, title_y))
        
    def _draw_instructions(self, surface):
        """Instructions avec fond semi-transparent."""
        # Fond semi-transparent
        instructions_bg = pygame.Surface((SCREEN_WIDTH, 100))
        instructions_bg.set_alpha(180)
        instructions_bg.fill((20, 20, 30))
        surface.blit(instructions_bg, (0, SCREEN_HEIGHT - 100))
        
        instructions = [
            "← → FLECHES pour naviguer",
            "ENTREE pour confirmer ton choix"
        ]
        
        instruction_y = SCREEN_HEIGHT - 75
        for instruction in instructions:
            text = self.font_instruction.render(instruction, True, WHITE)
            text_x = (SCREEN_WIDTH - text.get_width()) // 2
            surface.blit(text, (text_x, instruction_y))
            instruction_y += 30
    
    def _draw_starter_card(self, surface, card, is_selected):
        """Carte ULTRA COMPACTE - VERSION FINALE."""
        x = card["x"]
        y = card["y"]
        width = card["width"]
        height = card["height"]
        pokemon_data = card["data"]
        pokemon_id = card["pokemon_id"]
        
        # Animation de levitation
        offset_y = -8 if is_selected else 0
        y += offset_y
        
        # Ombre portee
        shadow_rect = pygame.Rect(x + 5, y + 5, width, height)
        shadow_surface = pygame.Surface((width, height))
        shadow_surface.set_alpha(100)
        shadow_surface.fill((0, 0, 0))
        surface.blit(shadow_surface, shadow_rect.topleft)
        
        # Couleurs
        border_color = YELLOW if is_selected else (200, 200, 200)
        border_width = 6 if is_selected else 3
        
        # Fond de la carte
        card_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (40, 45, 55), card_rect, border_radius=15)
        pygame.draw.rect(surface, border_color, card_rect, border_width, border_radius=15)
        
        # ============ CONTENU ULTRA SERRÉ ============
        current_y = y + 10  # Marge du haut
        
        # 1. SPRITE
        if pokemon_id in self.starter_sprites:
            sprite = self.starter_sprites[pokemon_id]
            sprite_x = x + (width - sprite.get_width()) // 2
            surface.blit(sprite, (sprite_x, current_y))
            current_y += sprite.get_height()
        else:
            current_y += 106  # 96 + 10
        
        # 2. NOM
        name = pokemon_data["name"].capitalize()
        name_font = get_font(18)  # Font réduite
        name_shadow = name_font.render(name, True, (0, 0, 0))
        name_text = name_font.render(name, True, YELLOW if is_selected else WHITE)
        
        name_x = x + (width - name_text.get_width()) // 2
        surface.blit(name_shadow, (name_x + 2, current_y + 2))
        surface.blit(name_text, (name_x, current_y))
        current_y += name_text.get_height() + 8
        
        # 3. TYPES
        badge_height = self._draw_type_badges(surface, pokemon_data["types"], x, current_y, width)
        current_y += badge_height + 10
        
        # 4. STATS (DANS LA CARTE !)
        stats = pokemon_data["stats"]
        stat_font = get_font(14)  # Font réduite
        
        stats_info = [
            f"HP: {stats['hp']}",
            f"ATT: {stats['attack']}",
            f"DEF: {stats['defense']}"
        ]
        
        # Vérifier qu'on ne dépasse pas
        max_y = y + height - 20  # Marge du bas de 20px
        
        for stat_line in stats_info:
            # Ne dessiner que si on a la place
            if current_y + 16 <= max_y:
                stat_text = stat_font.render(stat_line, True, (220, 220, 220))
                stat_x = x + (width - stat_text.get_width()) // 2
                surface.blit(stat_text, (stat_x, current_y))
                current_y += 16  # Espacement minimal
    
    def _draw_type_badges(self, surface, types, x, y, card_width):
        """Badges de types COMPACTS."""
        from config import TYPE_COLORS
        
        badge_width = 65  # Réduit encore
        badge_height = 20  # Réduit encore
        spacing = 6
        
        total_width = (badge_width * len(types)) + (spacing * (len(types) - 1))
        start_x = x + (card_width - total_width) // 2
        
        for i, poke_type in enumerate(types):
            badge_x = start_x + (i * (badge_width + spacing))
            badge_rect = pygame.Rect(badge_x, y, badge_width, badge_height)
            
            type_color = TYPE_COLORS.get(poke_type, (150, 150, 150))
            pygame.draw.rect(surface, type_color, badge_rect, border_radius=10)
            
            type_font = get_font(12)  # Font encore plus petite
            type_text = type_font.render(poke_type.upper(), True, WHITE)
            text_x = badge_x + (badge_width - type_text.get_width()) // 2
            text_y = y + (badge_height - type_text.get_height()) // 2
            surface.blit(type_text, (text_x, text_y))
        
        return badge_height