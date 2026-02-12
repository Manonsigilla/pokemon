"""Constantes globales du jeu Pokemon Battle Arena."""

import os

# --- Ecran ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TITLE = "Pokemon Battle Arena"

# --- Chemins ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
GAME_FONT = os.path.join(FONTS_DIR, "PKMN_RBYGSC.ttf")

# --- API ---
API_BASE_URL = "https://pokeapi.co/api/v2"
SPRITE_URL_FRONT = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{id}.png"
SPRITE_URL_BACK = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/{id}.png"

# Pool de Pokemon disponibles (Gen 1 populaires)
AVAILABLE_POKEMON_IDS = [
    1, 4, 7,      # Starters (Bulbasaur, Charmander, Squirtle)
    3, 6, 9,      # Evolutions finales (Venusaur, Charizard, Blastoise)
    25, 26,       # Pikachu, Raichu
    59,           # Arcanine
    65,           # Alakazam
    68,           # Machamp
    76,           # Golem
    94,           # Gengar
    103,          # Exeggutor
    112,          # Rhydon
    121,          # Starmie
    130,          # Gyarados
    131,          # Lapras
    143,          # Snorlax
    149,          # Dragonite
]

# Niveau par defaut
DEFAULT_LEVEL = 50

# --- Couleurs ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (208, 56, 56)
GREEN = (56, 168, 56)
YELLOW = (248, 208, 48)
BLUE = (56, 88, 200)
GRAY = (168, 168, 168)
DARK_GRAY = (88, 88, 88)
LIGHT_GRAY = (200, 200, 200)

# Couleurs HP
HP_GREEN = (0, 200, 0)
HP_YELLOW = (255, 200, 0)
HP_RED = (200, 0, 0)

# Style GBA
BG_LIGHT = (248, 248, 216)
BG_DARK = (64, 64, 64)
BORDER_COLOR = (40, 40, 40)
TEXT_BOX_BG = (248, 248, 216)
MENU_BG = (255, 255, 255)

# Couleurs des types Pokemon
TYPE_COLORS = {
    "normal": (168, 168, 120),
    "fire": (240, 128, 48),
    "water": (104, 144, 240),
    "grass": (120, 200, 80),
    "electric": (248, 208, 48),
    "ice": (152, 216, 216),
    "fighting": (192, 48, 40),
    "poison": (160, 64, 160),
    "ground": (224, 192, 104),
    "flying": (168, 144, 240),
    "psychic": (248, 88, 136),
    "bug": (168, 184, 32),
    "rock": (184, 160, 56),
    "ghost": (112, 88, 152),
    "dragon": (112, 56, 248),
    "dark": (112, 88, 72),
    "steel": (184, 184, 208),
    "fairy": (238, 153, 172),
}

# --- Positions de combat ---
PLAYER_SPRITE_POS = (100, 250)
ENEMY_SPRITE_POS = (500, 60)

PLAYER_INFO_POS = (460, 280)
ENEMY_INFO_POS = (30, 30)

TEXT_BOX_RECT = (0, 430, 800, 170)
MOVE_MENU_RECT = (400, 430, 400, 170)
MOVE_TEXT_RECT = (0, 430, 400, 170)

# --- Taille des sprites ---
SPRITE_SCALE = 3
