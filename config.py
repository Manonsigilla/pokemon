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

# Pool de Pokemon disponibles (Gen 1)
AVAILABLE_POKEMON_IDS = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151
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

# --- Positions de combat (POSITIONS ORIGINALES) ---
PLAYER_SPRITE_POS = (100, 250)
ENEMY_SPRITE_POS = (500, 60)

PLAYER_INFO_POS = (460, 280)  # HP bar joueur (en haut à droite)
ENEMY_INFO_POS = (30, 30)     # HP bar ennemi (en haut à gauche)

TEXT_BOX_RECT = (0, 430, 800, 170)
MOVE_MENU_RECT = (400, 430, 400, 170)
MOVE_TEXT_RECT = (0, 430, 400, 170)

# --- Animation ---
ATTACK_ANIMATION_SPEED = 3.0
SHAKE_INTENSITY = 12
PARTICLE_COLOR = (255, 255, 100)