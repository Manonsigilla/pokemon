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

def fit_text(text, max_width, max_size, min_size=8):
    """Trouve la plus grande taille de police pour que le texte rentre dans max_width.
    
    Args:
        text (str): Le texte à afficher
        max_width (int): Largeur maximale disponible en pixels
        max_size (int): Taille de police maximale souhaitée
        min_size (int): Taille de police minimale (défaut 8)
    
    Returns:
        pygame.font.Font: La police adaptée
    """
    for size in range(max_size, min_size - 1, -1):
        font = get_font(size)
        if font.size(text)[0] <= max_width:
            return font
    return get_font(min_size)


def render_fitted_text(text, max_width, max_size, color, min_size=8):
    """Rend un texte avec une taille de police adaptée automatiquement.
    
    Args:
        text (str): Le texte à afficher
        max_width (int): Largeur maximale disponible en pixels
        max_size (int): Taille de police maximale souhaitée
        color (tuple): Couleur RGB du texte
        min_size (int): Taille de police minimale (défaut 8)
    
    Returns:
        pygame.Surface: Le texte rendu
    """
    font = fit_text(text, max_width, max_size, min_size)
    return font.render(text, True, color)

# --- Images UI (titre + boutons) ---
TITLE_LOGO = os.path.join(IMAGES_DIR, "title_logo.png")
BTN_NORMAL = os.path.join(IMAGES_DIR, "btn_normal.png")
BTN_HOVER = os.path.join(IMAGES_DIR, "btn_hover.png")

# --- Fonds d'ecran ---
BG_MENU = os.path.join(IMAGES_DIR, "bg_menu.png")
BG_SELECTION = os.path.join(IMAGES_DIR, "bg_selection.jpg")

# --- Boutons menu principal ---
BTN_NVAVENTURE = os.path.join(IMAGES_DIR, "btn_nvaventure.png")
BTN_NVAVENTURE_HOVER = os.path.join(IMAGES_DIR, "btn_nvaventure_hover.png")
BTN_AVENTURE = os.path.join(IMAGES_DIR, "btn_aventure.png")
BTN_AVENTURE_HOVER = os.path.join(IMAGES_DIR, "btn_aventure_hover.png")
BTN_PVP = os.path.join(IMAGES_DIR, "btn_pvp.png")
BTN_PVP_HOVER = os.path.join(IMAGES_DIR, "btn_pvp_hover.png")
BTN_IA = os.path.join(IMAGES_DIR, "btn_ia.png")
BTN_IA_HOVER = os.path.join(IMAGES_DIR, "btn_ia_hover.png")

# --- Boutons difficulte ---
BTN_FACILE = os.path.join(IMAGES_DIR, "btn_facile.png")
BTN_FACILE_HOVER = os.path.join(IMAGES_DIR, "btn_facile_hover.png")
BTN_NORMAL = os.path.join(IMAGES_DIR, "btn_normal.png")
BTN_NORMAL_HOVER = os.path.join(IMAGES_DIR, "btn_normal_hover.png")
BTN_DIFFICILE = os.path.join(IMAGES_DIR, "btn_difficile.png")
BTN_DIFFICILE_HOVER = os.path.join(IMAGES_DIR, "btn_difficile_hover.png")