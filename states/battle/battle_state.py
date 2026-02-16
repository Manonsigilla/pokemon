"""Ecran de combat Pokemon style GBA - Equipes + Arenes + Animations."""

import random
import pygame

from states.state import State
from battle.battle import Battle
from battle.ai import AIOpponent
from ui.action_menu import ActionMenu      # Manon
from ui.team_menu import TeamMenu          # Manon
from ui.sprite_loader import SpriteLoader
from ui.sound_manager import sound_manager
from config import (SCREEN_WIDTH, SCREEN_HEIGHT,
                    PLAYER_SPRITE_POS, ENEMY_SPRITE_POS,
                    ARENA_BACKGROUNDS, MOVE_MENU_RECT, get_font)

from states.battle.constants import (
    PHASE_INTRO, PHASE_ACTION_P1, PHASE_ACTION_P2,
    PHASE_FORCE_SWITCH, PHASE_RESULT, PHASE_ANIMATE
)
from states.battle.battle_renderer import BattleRenderer
from states.battle.battle_input import BattleInput
from states.battle.battle_logic import BattleLogic
from states.battle.battle_animation import BattleAnimation


class BattleState(BattleRenderer, BattleInput, BattleLogic, BattleAnimation, State):
    """Gere l'affichage et l'interaction du combat avec equipes et animations."""

    def __init__(self, state_manager, type_chart):
        super().__init__(state_manager)
        self.type_chart = type_chart
        self.battle = None
        self.ai = None
        self.sprite_loader = SpriteLoader()

        self.phase = PHASE_INTRO
        self.hp_bar_p1 = None
        self.hp_bar_p2 = None
        self.text_box = None
        self.move_menu = None
        self.action_menu = None   # Manon
        self.team_menu = None     # Manon

        self.player_sprite = None
        self.enemy_sprite = None

        self.message_queue = []
        self.current_message_index = 0

        self.move_p1 = None
        self.move_p2 = None

        # Louis : fond d'arene
        self.background_image = None

        # Angie : positions sprites animees
        self.player_sprite_pos = list(PLAYER_SPRITE_POS)
        self.enemy_sprite_pos = list(ENEMY_SPRITE_POS)

        # Angie : systeme d'animation
        self.current_attacker = None  # "player" ou "enemy"
        self.attack_animation = None
        self.shake_animation = None
        self.impact_particles = []
        self.damage_numbers = []
        self.effectiveness_flash = None

        # Angie : ordre des attaques dans un tour
        self.turn_order = []
        self.current_turn_index = 0

        self._attack_missed = False
        self._last_result = None

        # Louis : flash d'attaque (fallback si pas d'animations Angie)
        self.flash_alpha = 0
        self.flash_timer = 0

        # Manon : switch force et fuite
        self._force_switch_player = None
        self._fleeing = False

        self._font_controls = None

    @property
    def font_controls(self):
        if self._font_controls is None:
            self._font_controls = get_font(10)
        return self._font_controls

    # =========================================================================
    # INITIALISATION
    # =========================================================================

    def enter(self):
        """Initialise le combat avec les equipes selectionnees."""
        sound_manager.stop_music()
        player1 = self.state_manager.shared_data["player1"]
        player2 = self.state_manager.shared_data["player2"]
        mode = self.state_manager.shared_data.get("mode", "pvp")

        # Creer le combat avec les Players (Manon)
        self.battle = Battle(player1, player2, self.type_chart, battle_type="arena")

        # IA si mode PvIA
        self.ai_difficulty = self.state_manager.shared_data.get("ai_difficulty", "normal")
        if mode == "pvia":
            self.ai = AIOpponent(
                self.battle.pokemon2, self.type_chart,
                difficulty=self.ai_difficulty,
                team=self.battle.player2.team
            )
        else:
            self.ai = None

        # Louis : charger le fond d'arene aleatoire
        arena_path = random.choice(ARENA_BACKGROUNDS)
        try:
            bg = pygame.image.load(arena_path).convert()
            self.background_image = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            self.background_image = None

        # Charger les sprites
        self._load_sprites()

        # Angie : reset positions sprites
        self.player_sprite_pos = list(PLAYER_SPRITE_POS)
        self.enemy_sprite_pos = list(ENEMY_SPRITE_POS)

        # Creer les widgets UI
        self._create_ui()

        # Manon : menus supplementaires
        self.action_menu = ActionMenu(*MOVE_MENU_RECT)
        self.team_menu = TeamMenu()

        # Phase d'intro
        self.phase = PHASE_INTRO
        self.message_queue = [
            f"Combat d'arene : {player1.name} VS {player2.name} !",
            f"{player2.name} envoie {self.battle.pokemon2.name} !",
            f"A toi, {self.battle.pokemon1.name} !",
        ]
        self.current_message_index = 0
        self.text_box.set_text(self.message_queue[0])

        self.move_p1 = None
        self.move_p2 = None
        self._force_switch_player = None
        self._fleeing = False

        # Angie : reset animations
        self.attack_animation = None
        self.shake_animation = None
        self.impact_particles = []
        self.damage_numbers = []
        self.effectiveness_flash = None
        self.turn_order = []
        self.current_turn_index = 0
        self._attack_missed = False
        self._last_result = None

    # =========================================================================
    # ORCHESTRATION DES PHASES
    # =========================================================================

    def _enter_action_phase(self):
        """Affiche le menu Combat / Pokemon / Fuite pour le joueur 1."""
        self.phase = PHASE_ACTION_P1
        self.action_menu.selected_index = 0
        self.action_menu.visible = True
        self.move_menu.visible = False
        self.move_p1 = None
        self.move_p2 = None
        self.text_box.set_text(f"Que doit faire {self.battle.pokemon1.name} ?")

    def _enter_action_p2(self):
        """Affiche le menu d'action pour le joueur 2."""
        self.phase = PHASE_ACTION_P2
        self.action_menu.selected_index = 0
        self.action_menu.visible = True
        self.move_menu.visible = False
        self.text_box.set_text(f"Que doit faire {self.battle.pokemon2.name} ?")

    def _open_force_switch(self, player_num):
        """Manon : Ouvre le menu de switch force apres un KO."""
        self.phase = PHASE_FORCE_SWITCH
        self._force_switch_player = player_num

        if player_num == 2 and self.ai:
            # L'IA choisit le meilleur Pokemon selon la difficulte
            alive = self.battle.player2.get_alive_pokemon()
            if alive:
                best = self.ai.choose_switch_after_ko(alive, self.battle.pokemon1)
                messages = self.battle.switch_pokemon(2, best)
                self._refresh_ui_after_switch(2)
                self._force_switch_player = None
                self._show_messages(messages)
            return

        # Joueur humain : ouvrir le menu
        player = self.battle.player1 if player_num == 1 else self.battle.player2
        current = self.battle.pokemon1 if player_num == 1 else self.battle.pokemon2
        self.team_menu.open(
            player.team,
            current_pokemon=current,
            allow_cancel=False  # Pas le choix, il FAUT switch
        )

    def _handle_result(self, event):
        """Gere l'ecran de resultat."""
        if event.key == pygame.K_RETURN:
            # Manon : passer le Player gagnant + un Pokemon pour l'affichage
            self.state_manager.shared_data["winner_player"] = self.battle.winner
            self.state_manager.shared_data["loser_player"] = self.battle.loser
            if self.battle.winner:
                self.state_manager.shared_data["winner"] = (
                    self.battle.winner.get_active_pokemon() or self.battle.winner.team[0]
                )
                self.state_manager.shared_data["loser"] = (
                    self.battle.loser.get_active_pokemon() or self.battle.loser.team[0]
                )
            self.state_manager.change_state("result")

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _show_messages(self, messages):
        """Affiche une liste de messages dans la text box."""
        self.message_queue = messages
        self.current_message_index = 0
        self.phase = PHASE_ANIMATE

        if messages:
            self.text_box.set_text(messages[0])
