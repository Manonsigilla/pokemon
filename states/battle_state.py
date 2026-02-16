"""Ecran de combat Pokemon style GBA - Equipes + Arenes + Animations."""

import random
import pygame

from states.state import State
from battle.battle import Battle
from battle.ai import AIOpponent, AI_SWITCH
# Angie : animations de combat
from battle.animation import (AttackAnimation, ShakeAnimation,
                              ImpactParticles, EffectivenessFlash)
from ui.hp_bar import HPBar
from ui.text_box import TextBox
from ui.move_menu import MoveMenu
from ui.action_menu import ActionMenu      # Manon
from ui.team_menu import TeamMenu          # Manon
from ui.sprite_loader import SpriteLoader
from ui.damage_number import DamageNumber  # Angie
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, WHITE,
                    PLAYER_SPRITE_POS, ENEMY_SPRITE_POS,
                    PLAYER_INFO_POS, ENEMY_INFO_POS,
                    TEXT_BOX_RECT, MOVE_MENU_RECT, MOVE_TEXT_RECT,
                    ARENA_BACKGROUNDS, GAME_FONT, get_font)


# Phases du combat (fusion Manon + Angie)
PHASE_INTRO = "intro"
PHASE_ACTION_P1 = "action_p1"            # Manon : menu Combat / Pokemon / Fuite (J1)
PHASE_CHOOSE_P1 = "choose_p1"            # Selection attaque J1
PHASE_ACTION_P2 = "action_p2"            # Manon : menu Combat / Pokemon / Fuite (J2)
PHASE_CHOOSE_P2 = "choose_p2"            # Selection attaque J2
PHASE_SWITCH_P1 = "switch_p1"            # Manon : switch volontaire J1
PHASE_SWITCH_P2 = "switch_p2"            # Manon : switch volontaire J2
PHASE_FORCE_SWITCH = "force_switch"      # Manon : switch force apres KO
PHASE_EXECUTE_ANIMATION = "execute_anim" # Angie : animation d'attaque en cours
PHASE_SHOW_RESULTS = "show_results"      # Angie : messages de resultats apres animation
PHASE_ANIMATE = "animate"                # Messages generiques (switch, fuite, etc.)
PHASE_RESULT = "result"


class BattleState(State):
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

    def _load_sprites(self):
        """Charge les sprites des Pokemon actifs."""
        self.player_sprite = self.sprite_loader.load_sprite(
            self.battle.pokemon1.back_sprite_path
        )
        self.enemy_sprite = self.sprite_loader.load_sprite(
            self.battle.pokemon2.front_sprite_path
        )

    def _create_ui(self):
        """Cree les widgets UI pour les Pokemon actifs."""
        self.hp_bar_p2 = HPBar(
            ENEMY_INFO_POS[0], ENEMY_INFO_POS[1],
            250, self.battle.pokemon2, show_hp_text=False
        )
        self.hp_bar_p1 = HPBar(
            PLAYER_INFO_POS[0], PLAYER_INFO_POS[1],
            250, self.battle.pokemon1, show_hp_text=True
        )
        self.text_box = TextBox(*TEXT_BOX_RECT)
        self.move_menu = MoveMenu(*MOVE_MENU_RECT, self.battle.pokemon1.moves)

    def _refresh_ui_after_switch(self, player_num):
        """Manon : Met a jour les sprites et barres de vie apres un switch."""
        if player_num == 1:
            self.player_sprite = self.sprite_loader.load_sprite(
                self.battle.pokemon1.back_sprite_path
            )
            self.hp_bar_p1 = HPBar(
                PLAYER_INFO_POS[0], PLAYER_INFO_POS[1],
                250, self.battle.pokemon1, show_hp_text=True
            )
            # Angie : reset position sprite
            self.player_sprite_pos = list(PLAYER_SPRITE_POS)
        else:
            self.enemy_sprite = self.sprite_loader.load_sprite(
                self.battle.pokemon2.front_sprite_path
            )
            self.hp_bar_p2 = HPBar(
                ENEMY_INFO_POS[0], ENEMY_INFO_POS[1],
                250, self.battle.pokemon2, show_hp_text=False
            )
            # Angie : reset position sprite
            self.enemy_sprite_pos = list(ENEMY_SPRITE_POS)
            # Manon : mettre a jour l'IA
            if self.ai:
                self.ai = AIOpponent(
                    self.battle.pokemon2, self.type_chart,
                    difficulty=self.ai_difficulty,
                    team=self.battle.player2.team
                )

    # =========================================================================
    # GESTION DES EVENEMENTS
    # =========================================================================

    def handle_events(self, events):
        """Gere les inputs selon la phase courante."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Manon : le team menu a priorite quand il est ouvert
                if self.team_menu and self.team_menu.visible:
                    self._handle_team_menu(event)
                    return

                if self.phase == PHASE_INTRO:
                    self._handle_message_advance(event)

                elif self.phase == PHASE_ACTION_P1:
                    self._handle_action_p1(event)

                elif self.phase == PHASE_CHOOSE_P1:
                    self._handle_choose_p1(event)

                elif self.phase == PHASE_ACTION_P2:
                    self._handle_action_p2(event)

                elif self.phase == PHASE_CHOOSE_P2:
                    self._handle_choose_p2(event)

                elif self.phase == PHASE_ANIMATE:
                    self._handle_message_advance(event)

                elif self.phase == PHASE_SHOW_RESULTS:
                    self._handle_results_input(event)

                elif self.phase == PHASE_RESULT:
                    self._handle_result(event)
                # Note: PHASE_EXECUTE_ANIMATION n'a pas d'input, c'est automatique

    def _handle_message_advance(self, event):
        """Avance dans la file de messages."""
        if event.key in (pygame.K_SPACE, pygame.K_RETURN):
            if not self.text_box.is_complete:
                self.text_box.skip_animation()
                return

            self.current_message_index += 1
            if self.current_message_index < len(self.message_queue):
                self.text_box.set_text(self.message_queue[self.current_message_index])
            else:
                # Fin des messages
                if self.phase == PHASE_INTRO:
                    self._enter_action_phase()
                elif self.phase == PHASE_ANIMATE:
                    # Manon : verifier fuite
                    if self._fleeing:
                        self._fleeing = False
                        self.state_manager.change_state("title")
                        return

                    if self.battle.is_over:
                        self.phase = PHASE_RESULT
                        self.text_box.set_text("Appuyez sur Entree pour continuer...")
                    else:
                        # Manon : verifier si un Pokemon est KO et doit etre remplace
                        fainted = self.battle.get_fainted_player()
                        if fainted is not None:
                            self._open_force_switch(fainted)
                        else:
                            self._enter_action_phase()

    # --- Manon : Menu d'action principal ---

    def _enter_action_phase(self):
        """Affiche le menu Combat / Pokemon / Fuite pour le joueur 1."""
        self.phase = PHASE_ACTION_P1
        self.action_menu.selected_index = 0
        self.action_menu.visible = True
        self.move_menu.visible = False
        self.move_p1 = None
        self.move_p2 = None
        self.text_box.set_text(f"Que doit faire {self.battle.pokemon1.name} ?")

    def _handle_action_p1(self, event):
        """Manon : Joueur 1 choisit une action avec WASD + Espace."""
        if event.key == pygame.K_w:
            self.action_menu.navigate("up")
        elif event.key == pygame.K_s:
            self.action_menu.navigate("down")
        elif event.key == pygame.K_SPACE:
            action = self.action_menu.get_selected_action()
            self.action_menu.visible = False

            if action == "combat":
                self.phase = PHASE_CHOOSE_P1
                self.move_menu.moves = self.battle.pokemon1.moves
                self.move_menu.selected_index = 0
                self.move_menu.visible = True
            elif action == "pokemon":
                self.phase = PHASE_SWITCH_P1
                switchable = self.battle.player1.get_switchable_pokemon(self.battle.pokemon1)
                if switchable:
                    self.team_menu.open(
                        self.battle.player1.team,
                        current_pokemon=self.battle.pokemon1,
                        allow_cancel=True
                    )
                else:
                    self._show_messages(["Aucun autre Pokemon disponible !"])
            elif action == "fuite":
                if self.battle.battle_type == "arena":
                    self._show_messages(["Impossible de fuir un combat d'arene !"])
                else:
                    self._flee_battle()

    def _handle_choose_p1(self, event):
        """Joueur 1 choisit une attaque avec WASD + Espace."""
        if event.key == pygame.K_w:
            self.move_menu.navigate("up")
        elif event.key == pygame.K_s:
            self.move_menu.navigate("down")
        elif event.key == pygame.K_a:
            self.move_menu.navigate("left")
        elif event.key == pygame.K_d:
            self.move_menu.navigate("right")
        elif event.key == pygame.K_ESCAPE:
            self.move_menu.visible = False
            self._enter_action_phase()
        elif event.key == pygame.K_SPACE:
            move = self.move_menu.get_selected_move()
            if move.has_pp():
                self.move_p1 = move
                self.move_menu.visible = False

                if self.ai:
                    # L'IA choisit automatiquement (peut decider de switcher)
                    switchable = self.battle.player2.get_switchable_pokemon(
                        self.battle.pokemon2
                    )
                    action, switch_target = self.ai.choose_action(
                        self.battle.pokemon1, switchable
                    )

                    if action == AI_SWITCH and switch_target:
                        # L'IA decide de switcher volontairement
                        messages = self.battle.switch_pokemon(2, switch_target)
                        self._refresh_ui_after_switch(2)
                        # Le joueur attaque le nouveau Pokemon
                        msgs_attack = self.battle._process_turn(
                            self.battle.pokemon1, self.battle.pokemon2, self.move_p1
                        )
                        self.move_p1.use()
                        messages.extend(msgs_attack)
                        if self.battle.pokemon2.is_fainted():
                            messages.append(f"{self.battle.pokemon2.name} est K.O. !")
                            if not self.battle.player2.has_alive_pokemon():
                                self.battle.is_over = True
                                self.battle.winner = self.battle.player1
                                self.battle.loser = self.battle.player2
                                messages.append(
                                    f"{self.battle.player1.name} remporte le combat !"
                                )
                        self._show_messages(messages)
                    else:
                        self.move_p2 = action
                        # Angie : determiner l'ordre et lancer les animations
                        self._determine_turn_order()
                        self._execute_next_attack()
                else:
                    # Manon : passer au joueur 2 - menu d'action
                    self._enter_action_p2()

    # --- Manon : Menu d'action Joueur 2 (PvP) ---

    def _enter_action_p2(self):
        """Affiche le menu d'action pour le joueur 2."""
        self.phase = PHASE_ACTION_P2
        self.action_menu.selected_index = 0
        self.action_menu.visible = True
        self.move_menu.visible = False
        self.text_box.set_text(f"Que doit faire {self.battle.pokemon2.name} ?")

    def _handle_action_p2(self, event):
        """Manon : Joueur 2 choisit une action avec Fleches + Entree."""
        if event.key == pygame.K_UP:
            self.action_menu.navigate("up")
        elif event.key == pygame.K_DOWN:
            self.action_menu.navigate("down")
        elif event.key == pygame.K_RETURN:
            action = self.action_menu.get_selected_action()
            self.action_menu.visible = False

            if action == "combat":
                self.phase = PHASE_CHOOSE_P2
                self.move_menu.moves = self.battle.pokemon2.moves
                self.move_menu.selected_index = 0
                self.move_menu.visible = True
            elif action == "pokemon":
                self.phase = PHASE_SWITCH_P2
                switchable = self.battle.player2.get_switchable_pokemon(self.battle.pokemon2)
                if switchable:
                    self.team_menu.open(
                        self.battle.player2.team,
                        current_pokemon=self.battle.pokemon2,
                        allow_cancel=True
                    )
                else:
                    self._show_messages(["Aucun autre Pokemon disponible !"])
            elif action == "fuite":
                if self.battle.battle_type == "arena":
                    self._show_messages(["Impossible de fuir un combat d'arene !"])
                else:
                    self._flee_battle()

    def _handle_choose_p2(self, event):
        """Joueur 2 choisit une attaque avec Fleches + Entree."""
        if event.key == pygame.K_UP:
            self.move_menu.navigate("up")
        elif event.key == pygame.K_DOWN:
            self.move_menu.navigate("down")
        elif event.key == pygame.K_LEFT:
            self.move_menu.navigate("left")
        elif event.key == pygame.K_RIGHT:
            self.move_menu.navigate("right")
        elif event.key == pygame.K_ESCAPE:
            self.move_menu.visible = False
            self._enter_action_p2()
        elif event.key == pygame.K_RETURN:
            move = self.move_menu.get_selected_move()
            if move.has_pp():
                self.move_p2 = move
                self.move_menu.visible = False
                # Angie : determiner l'ordre et lancer les animations
                self._determine_turn_order()
                self._execute_next_attack()

    # --- Manon : Fuite ---

    def _flee_battle(self):
        """Gere la fuite du combat."""
        self._fleeing = True
        self._show_messages(["Vous prenez la fuite !"])

    # --- Manon : Menu d'equipe (switch) ---

    def _handle_team_menu(self, event):
        """Manon : Gere les inputs dans le menu d'equipe."""
        if event.key in (pygame.K_UP, pygame.K_w):
            self.team_menu.navigate("up")
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.team_menu.navigate("down")
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            selected = self.team_menu.get_selected_pokemon()
            if selected:
                self.team_menu.close()
                self._perform_switch(selected)
        elif event.key == pygame.K_ESCAPE:
            if self.team_menu.allow_cancel:
                self.team_menu.close()
                if self.phase == PHASE_SWITCH_P1:
                    self._enter_action_phase()
                elif self.phase == PHASE_SWITCH_P2:
                    self._enter_action_p2()
            # Si force_switch, on ne peut pas annuler

    def _perform_switch(self, new_pokemon):
        """Manon : Execute le switch et continue le combat."""
        if self.phase == PHASE_SWITCH_P1:
            # Switch volontaire P1 : l'adversaire attaque pendant le switch
            messages = self.battle.switch_pokemon(1, new_pokemon)
            self._refresh_ui_after_switch(1)

            if self.ai:
                # L'IA attaque pendant le switch du joueur (pas de switch IA ici)
                self.move_p2 = self.ai.choose_move(self.battle.pokemon1)
                msgs_attack = self.battle._process_turn(
                    self.battle.pokemon2, self.battle.pokemon1, self.move_p2
                )
                messages.extend(msgs_attack)

                if self.battle.pokemon1.is_fainted():
                    messages.append(f"{self.battle.pokemon1.name} est K.O. !")
                    if not self.battle.player1.has_alive_pokemon():
                        self.battle.is_over = True
                        self.battle.winner = self.battle.player2
                        self.battle.loser = self.battle.player1
                        messages.append(f"{self.battle.player2.name} remporte le combat !")

            self._show_messages(messages)

        elif self.phase == PHASE_SWITCH_P2:
            # Switch volontaire P2
            messages = self.battle.switch_pokemon(2, new_pokemon)
            self._refresh_ui_after_switch(2)
            self._show_messages(messages)

        elif self.phase == PHASE_FORCE_SWITCH:
            # Switch force apres KO
            player_num = self._force_switch_player
            messages = self.battle.switch_pokemon(player_num, new_pokemon)
            self._refresh_ui_after_switch(player_num)
            self._force_switch_player = None
            self._show_messages(messages)

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

    # --- Resultat ---

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
    # Angie : SYSTEME D'ANIMATION DES ATTAQUES
    # =========================================================================

    def _determine_turn_order(self):
        """Angie : Determine qui attaque en premier selon la vitesse."""
        p1 = self.battle.pokemon1
        p2 = self.battle.pokemon2

        speed1 = p1.get_effective_speed()
        speed2 = p2.get_effective_speed()

        if speed1 > speed2:
            self.turn_order = [
                (p1, self.move_p1, True),
                (p2, self.move_p2, False)
            ]
        elif speed2 > speed1:
            self.turn_order = [
                (p2, self.move_p2, False),
                (p1, self.move_p1, True)
            ]
        else:
            if random.random() < 0.5:
                self.turn_order = [
                    (p1, self.move_p1, True),
                    (p2, self.move_p2, False)
                ]
            else:
                self.turn_order = [
                    (p2, self.move_p2, False),
                    (p1, self.move_p1, True)
                ]

        self.current_turn_index = 0

    def _execute_next_attack(self):
        """Angie : Lance l'attaque suivante dans l'ordre."""
        if self.current_turn_index >= len(self.turn_order):
            # Les deux Pokemon ont attaque -> fin du tour
            self._end_turn()
            return

        attacker, move, is_player = self.turn_order[self.current_turn_index]

        # Verifier si l'attaquant est KO
        if attacker.is_fainted():
            self.current_turn_index += 1
            self._execute_next_attack()
            return

        # Definir attaquant
        self.current_attacker = "player" if is_player else "enemy"

        # Message d'attaque
        self.text_box.set_text(f"{attacker.name} utilise {move.display_name} !")

        # Utiliser le PP du move
        move.use()

        # Lancer l'animation d'attaque
        if is_player:
            self.attack_animation = AttackAnimation(
                list(PLAYER_SPRITE_POS),
                list(ENEMY_SPRITE_POS),
                is_player=True
            )
        else:
            self.attack_animation = AttackAnimation(
                list(ENEMY_SPRITE_POS),
                list(PLAYER_SPRITE_POS),
                is_player=False
            )

        self.phase = PHASE_EXECUTE_ANIMATION

    def _apply_attack_damage(self):
        """Angie : Applique les degats et lance les animations d'impact."""
        attacker, move, is_player = self.turn_order[self.current_turn_index]
        defender = self.battle.pokemon2 if is_player else self.battle.pokemon1

        # Verifier la precision
        if random.randint(1, 100) > move.accuracy:
            self._attack_missed = True
            return

        self._attack_missed = False

        # Calculer les degats
        if move.is_damaging():
            result = self.battle.damage_calc.calculate(attacker, defender, move)
            defender.take_damage(result.damage)

            self._last_result = result

            # Position du defenseur pour les animations
            defender_pos = list(ENEMY_SPRITE_POS) if is_player else list(PLAYER_SPRITE_POS)

            # Shake
            self.shake_animation = ShakeAnimation(
                tuple(defender_pos),
                intensity=12 if result.damage > 50 else 8
            )

            # Particules
            particle_pos = (defender_pos[0] + 40, defender_pos[1] + 40)

            if result.effectiveness >= 2.0:
                particle_color = (100, 255, 100)
            elif result.effectiveness < 1.0 and result.effectiveness > 0:
                particle_color = (255, 100, 100)
            else:
                particle_color = (255, 255, 100)

            self.impact_particles.append(ImpactParticles(particle_pos, particle_color))

            # Degats flottants
            dmg_pos = (particle_pos[0], particle_pos[1] - 20)
            self.damage_numbers.append(
                DamageNumber(
                    result.damage,
                    dmg_pos,
                    is_critical=result.is_critical,
                    is_effective=result.effectiveness
                )
            )

            # Flash d'efficacite
            if result.effectiveness != 1.0:
                self.effectiveness_flash = EffectivenessFlash(result.effectiveness)

            # Appliquer le statut
            if move.ailment and result.effectiveness > 0:
                if move.ailment_chance > 0:
                    if random.randint(1, 100) <= move.ailment_chance:
                        defender.apply_status(move.ailment)
        else:
            self._last_result = None

    def _show_attack_results(self):
        """Angie : Affiche les messages de resultat de l'attaque."""
        attacker, move, is_player = self.turn_order[self.current_turn_index]
        defender = self.battle.pokemon2 if is_player else self.battle.pokemon1

        messages = []

        if self._attack_missed:
            messages.append(f"L'attaque de {attacker.name} a echoue !")
        elif self._last_result:
            result = self._last_result

            if result.effectiveness == 0:
                messages.append("Ca n'a aucun effet...")
            else:
                messages.append(f"{defender.name} perd {result.damage} PV !")

                eff_text = self.type_chart.get_effectiveness_text(result.effectiveness)
                if eff_text:
                    messages.append(eff_text)

                if result.is_critical:
                    messages.append("Coup critique !")

        # Manon : verifier KO avec systeme d'equipes
        if defender.is_fainted():
            messages.append(f"{defender.name} est K.O. !")

            # Determiner le Player perdant
            loser_player = self.battle.player2 if defender == self.battle.pokemon2 else self.battle.player1
            winner_player = self.battle.player1 if loser_player == self.battle.player2 else self.battle.player2

            if not loser_player.has_alive_pokemon():
                self.battle.is_over = True
                self.battle.winner = winner_player
                self.battle.loser = loser_player
                messages.append(f"{winner_player.name} remporte le combat !")
            else:
                messages.append(f"{loser_player.name} doit envoyer un autre Pokemon !")

        if messages:
            self.message_queue = messages
            self.current_message_index = 0
            self.text_box.set_text(messages[0])
            self.phase = PHASE_SHOW_RESULTS
        else:
            self.current_turn_index += 1
            self._execute_next_attack()

    def _handle_results_input(self, event):
        """Angie : Avance dans les messages de resultats."""
        if event.key in (pygame.K_SPACE, pygame.K_RETURN):
            if not self.text_box.is_complete:
                self.text_box.skip_animation()
                return

            self.current_message_index += 1
            if self.current_message_index < len(self.message_queue):
                self.text_box.set_text(self.message_queue[self.current_message_index])
            else:
                # Fin des messages
                if self.battle.is_over:
                    self.phase = PHASE_RESULT
                    self.text_box.set_text("Appuyez sur Entree pour continuer...")
                else:
                    # Manon : verifier si un Pokemon est KO et doit etre remplace
                    fainted = self.battle.get_fainted_player()
                    if fainted is not None:
                        self._open_force_switch(fainted)
                    else:
                        # Passer a l'attaque suivante ou nouveau tour
                        self.current_turn_index += 1
                        self._execute_next_attack()

    def _end_turn(self):
        """Angie : Termine le tour et verifie les effets de statut."""
        messages = []

        for pokemon in [self.battle.pokemon1, self.battle.pokemon2]:
            if pokemon.status and pokemon.status.is_active:
                msg = pokemon.status.on_turn_end(pokemon)
                if msg:
                    messages.append(msg)
                if not pokemon.status.is_active:
                    pokemon.status = None

                if pokemon.is_fainted():
                    messages.append(f"{pokemon.name} est K.O. !")

                    # Manon : determiner le Player perdant
                    loser_player = self.battle.player1 if pokemon == self.battle.pokemon1 else self.battle.player2
                    winner_player = self.battle.player2 if loser_player == self.battle.player1 else self.battle.player1

                    if not loser_player.has_alive_pokemon():
                        self.battle.is_over = True
                        self.battle.winner = winner_player
                        self.battle.loser = loser_player
                        messages.append(f"{winner_player.name} remporte le combat !")
                    else:
                        messages.append(f"{loser_player.name} doit envoyer un autre Pokemon !")
                    break

        if messages:
            self.message_queue = messages
            self.current_message_index = 0
            self.text_box.set_text(messages[0])
            self.phase = PHASE_SHOW_RESULTS
        else:
            self._enter_action_phase()

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

    # =========================================================================
    # UPDATE & DRAW
    # =========================================================================

    def update(self, dt):
        """Met a jour les animations."""
        self.text_box.update(dt)
        self.hp_bar_p1.update(dt)
        self.hp_bar_p2.update(dt)

        # Louis : flash d'attaque
        if self.flash_timer > 0:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.flash_alpha = 0

        # Angie : animations d'attaque
        if self.phase == PHASE_EXECUTE_ANIMATION:
            all_animations_done = True

            # Attack animation
            if self.attack_animation:
                self.attack_animation.update(dt)

                if self.current_attacker == "player":
                    self.player_sprite_pos = list(self.attack_animation.get_attacker_position())
                else:
                    self.enemy_sprite_pos = list(self.attack_animation.get_attacker_position())

                if self.attack_animation.should_show_impact() and not self.shake_animation:
                    self._apply_attack_damage()

                if self.attack_animation.is_complete:
                    self.attack_animation = None
                else:
                    all_animations_done = False

            # Shake animation
            if self.shake_animation:
                self.shake_animation.update(dt)
                if self.current_attacker == "player":
                    self.enemy_sprite_pos = list(self.shake_animation.get_position())
                else:
                    self.player_sprite_pos = list(self.shake_animation.get_position())

                if self.shake_animation.is_complete:
                    if self.current_attacker == "player":
                        self.enemy_sprite_pos = list(ENEMY_SPRITE_POS)
                    else:
                        self.player_sprite_pos = list(PLAYER_SPRITE_POS)
                    self.shake_animation = None
                else:
                    all_animations_done = False

            # Particules
            for particle in self.impact_particles[:]:
                particle.update(dt)
                if particle.is_complete:
                    self.impact_particles.remove(particle)
            if self.impact_particles:
                all_animations_done = False

            # Degats flottants
            for dmg_num in self.damage_numbers[:]:
                dmg_num.update(dt)
                if dmg_num.is_complete:
                    self.damage_numbers.remove(dmg_num)
            if self.damage_numbers:
                all_animations_done = False

            # Flash d'efficacite
            if self.effectiveness_flash:
                self.effectiveness_flash.update(dt)
                if self.effectiveness_flash.is_complete:
                    self.effectiveness_flash = None
                else:
                    all_animations_done = False

            if all_animations_done:
                self._show_attack_results()

    def draw(self, surface):
        """Dessine l'ecran de combat complet."""
        # Louis : fond de l'arene
        self._draw_background(surface)

        # Angie : sprites aux positions animees
        if self.player_sprite:
            surface.blit(self.player_sprite, self.player_sprite_pos)
        if self.enemy_sprite:
            surface.blit(self.enemy_sprite, self.enemy_sprite_pos)

        # Barres de vie
        self.hp_bar_p1.draw(surface)
        self.hp_bar_p2.draw(surface)

        # Manon : indicateurs d'equipe (petites pokeballs)
        self._draw_team_indicators(surface)

        # Angie : particules d'impact
        for particles in self.impact_particles:
            particles.draw(surface)

        # Angie : degats flottants
        for dmg_num in self.damage_numbers:
            dmg_num.draw(surface)

        # Zone de texte / menus
        if self.action_menu and self.action_menu.visible:
            action_box = TextBox(*MOVE_TEXT_RECT)
            if self.phase == PHASE_ACTION_P1:
                action_box.set_text(f"Que doit faire {self.battle.pokemon1.name} ?")
            else:
                action_box.set_text(f"Que doit faire {self.battle.pokemon2.name} ?")
            action_box.skip_animation()
            action_box.draw(surface)
            self.action_menu.draw(surface)

            controls = "W/S + Espace" if self.phase == PHASE_ACTION_P1 else "Haut/Bas + Entree"
            ctrl_text = self.font_controls.render(controls, True, (100, 100, 100))
            surface.blit(ctrl_text, (10, SCREEN_HEIGHT - 18))

        elif self.move_menu and self.move_menu.visible:
            action_box = TextBox(*MOVE_TEXT_RECT)
            if self.phase == PHASE_CHOOSE_P1:
                action_box.set_text(f"Que doit faire {self.battle.pokemon1.name} ?")
            else:
                action_box.set_text(f"Que doit faire {self.battle.pokemon2.name} ?")
            action_box.skip_animation()
            action_box.draw(surface)
            self.move_menu.draw(surface)

            controls = "WASD + Espace | Echap = retour" if self.phase == PHASE_CHOOSE_P1 else "Fleches + Entree | Echap = retour"
            ctrl_text = self.font_controls.render(controls, True, (100, 100, 100))
            surface.blit(ctrl_text, (10, SCREEN_HEIGHT - 18))
        else:
            self.text_box.draw(surface)

        # Louis : flash d'attaque
        if self.flash_alpha > 0:
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surface.fill(WHITE)
            flash_surface.set_alpha(int(self.flash_alpha))
            surface.blit(flash_surface, (0, 0))

        # Angie : flash d'efficacite
        if self.effectiveness_flash:
            self.effectiveness_flash.draw(surface)

        # Manon : team menu en overlay (par dessus tout)
        if self.team_menu and self.team_menu.visible:
            self.team_menu.draw(surface)

    def _draw_team_indicators(self, surface):
        """Dessine des indicateurs (pokeballs) pour chaque Pokemon de l'equipe."""
        indicator_size = 12
        spacing = 18

        # Equipe J1 (sous la barre de vie du joueur, a gauche)
        start_x_p1 = 50
        y_p1 = PLAYER_SPRITE_POS[1] + 170  # Sous le sprite joueur
        for i, poke in enumerate(self.battle.player1.team):
            x = start_x_p1 + i * spacing
            if poke.is_fainted():
                color = (180, 50, 50)   # Rouge = KO
            elif poke == self.battle.pokemon1:
                color = (60, 200, 60)   # Vert = actif
            else:
                color = (220, 220, 220) # Blanc/gris = en reserve
            pygame.draw.circle(surface, color, (x, y_p1), indicator_size // 2)
            pygame.draw.circle(surface, (30, 30, 30), (x, y_p1), indicator_size // 2, 1)

        # Equipe J2 (sous la barre de vie de l'ennemi, a droite)
        # Positionner par rapport a ENEMY_INFO_POS pour que ce soit visible
        start_x_p2 = ENEMY_INFO_POS[0] + 200
        y_p2 = ENEMY_INFO_POS[1] + 60  # Juste sous le panneau ennemi
        for i, poke in enumerate(self.battle.player2.team):
            x = start_x_p2 + i * spacing
            if poke.is_fainted():
                color = (180, 50, 50)   # Rouge = KO
            elif poke == self.battle.pokemon2:
                color = (60, 200, 60)   # Vert = actif
            else:
                color = (220, 220, 220) # Blanc/gris = en reserve
            pygame.draw.circle(surface, color, (x, y_p2), indicator_size // 2)
            pygame.draw.circle(surface, (30, 30, 30), (x, y_p2), indicator_size // 2, 1)

    def _draw_background(self, surface):
        """Louis : Dessine le fond de l'arene avec l'image chargee."""
        if self.background_image:
            surface.blit(self.background_image, (0, 0))
        else:
            # Fallback GBA (Manon/Angie)
            surface.fill((136, 192, 240))
            pygame.draw.ellipse(surface, (144, 200, 120), (420, 230, 320, 60))
            pygame.draw.ellipse(surface, (120, 176, 100), (420, 230, 320, 60), 2)
            pygame.draw.ellipse(surface, (144, 200, 120), (20, 420, 350, 70))
            pygame.draw.ellipse(surface, (120, 176, 100), (20, 420, 350, 70), 2)
            pygame.draw.rect(surface, (120, 176, 100), (0, 430, SCREEN_WIDTH, 170))