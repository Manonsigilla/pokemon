"""Constantes globales du jeu Pokemon Battle Arena."""

import os
import pygame

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
IMAGES_DIR = os.path.join(BASE_DIR, "images")

# --- Police custom (Angie) ---
GAME_FONT = os.path.join(FONTS_DIR, "PKMN_RBYGSC.ttf")
if not os.path.exists(GAME_FONT):
    GAME_FONT = None

# --- Arenes (images de fond) - Louis ---
ARENA_BACKGROUNDS = [
    os.path.join(IMAGES_DIR, "image_foret.png"),
    os.path.join(IMAGES_DIR, "image_neige.png"),
    os.path.join(IMAGES_DIR, "image_plage.png"),
    os.path.join(IMAGES_DIR, "image_prairie.png"),
    os.path.join(IMAGES_DIR, "image_ruine.png"),
]

# --- API ---
API_BASE_URL = "https://pokeapi.co/api/v2"
SPRITE_URL_FRONT = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{id}.png"
SPRITE_URL_BACK = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/{id}.png"

# Pool de Pokemon disponibles (Gen 1)
AVAILABLE_POKEMON_IDS = list(range(1, 152))

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

# --- Positions de combat (Louis) ---
PLAYER_SPRITE_POS = (100, 250)
ENEMY_SPRITE_POS = (500, 110)

PLAYER_INFO_POS = (460, 380)
ENEMY_INFO_POS = (30, 30)

TEXT_BOX_RECT = (0, 490, 800, 110)
MOVE_MENU_RECT = (400, 490, 400, 110)
MOVE_TEXT_RECT = (0, 490, 400, 110)

# --- Taille des sprites ---
SPRITE_SCALE = 3

def get_font(size):
    """Charge la font Pokemon custom ou fallback sur la font systeme.
    
    La font PKMN_RBYGSC est une font bitmap : il faut utiliser des tailles
    plus petites que les fonts systeme pour un rendu lisible.
    """
    if GAME_FONT:
        return pygame.font.Font(GAME_FONT, size)
    return pygame.font.Font(None, size)