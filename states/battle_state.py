"""Ecran de combat Pokemon style GBA avec animations améliorées."""

import pygame
import os

from states.state import State
from battle.battle import Battle
from battle.ai import AIOpponent
from battle.animation import (AttackAnimation, ShakeAnimation, 
                            ImpactParticles, EffectivenessFlash)
from ui.hp_bar import HPBar
from ui.text_box import TextBox
from ui.move_menu import MoveMenu
from ui.sprite_loader import SpriteLoader
from ui.damage_number import DamageNumber
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BASE_DIR,
                    PLAYER_SPRITE_POS, ENEMY_SPRITE_POS,
                    PLAYER_INFO_POS, ENEMY_INFO_POS,
                    TEXT_BOX_RECT, MOVE_MENU_RECT)


# Phases du combat (tour par tour amélioré)
PHASE_INTRO = "intro"
PHASE_CHOOSE_MOVE = "choose_move"
PHASE_EXECUTE_ANIMATION = "execute_animation"
PHASE_SHOW_RESULTS = "show_results"
PHASE_END_TURN = "end_turn"
PHASE_GAME_OVER = "game_over"


class BattleState(State):
    """Gere l'affichage et l'interaction du combat avec animations."""

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

        self.player_sprite = None
        self.enemy_sprite = None
        
        # Background image
        self.background_image = None

        # Messages
        self.message_queue = []
        self.current_message_index = 0

        # Moves sélectionnés
        self.selected_move_p1 = None
        self.selected_move_p2 = None
        self.current_player = 1

        # Système d'animation
        self.current_attacker = None  # "player" ou "enemy"
        self.attack_animation = None
        self.shake_animation = None
        self.impact_particles = []
        self.damage_numbers = []
        self.effectiveness_flash = None
        
        # Turn order
        self.turn_order = []  # Liste de tuples (pokemon, move, is_player)
        self.current_turn_index = 0
        
        # Positions des sprites
        self.player_sprite_pos = list(PLAYER_SPRITE_POS)
        self.enemy_sprite_pos = list(ENEMY_SPRITE_POS)

        self._attack_missed = False
        self._last_result = None

    def enter(self):
        """Initialise le combat avec les Pokemon selectionnes."""
        pokemon1 = self.state_manager.shared_data["pokemon1"]
        pokemon2 = self.state_manager.shared_data["pokemon2"]
        mode = self.state_manager.shared_data.get("mode", "pvp")

        # Créer le combat
        self.battle = Battle(pokemon1, pokemon2, self.type_chart)

        # IA si mode PvIA
        if mode == "pvia":
            self.ai = AIOpponent(pokemon2, self.type_chart)
        else:
            self.ai = None

        # Charger le background
        try:
            bg_path = os.path.join(BASE_DIR, "assets", "backgrounds", "battle_bg.png")
            self.background_image = pygame.image.load(bg_path).convert()
            self.background_image = pygame.transform.scale(
                self.background_image, 
                (SCREEN_WIDTH, SCREEN_HEIGHT)
            )
        except Exception as e:
            print(f"Could not load background image: {e}")
            self.background_image = None

        # Charger les sprites
        self.player_sprite = self.sprite_loader.load_sprite(pokemon1.back_sprite_path)
        self.enemy_sprite = self.sprite_loader.load_sprite(pokemon2.front_sprite_path)
        
        # Reset positions
        self.player_sprite_pos = list(PLAYER_SPRITE_POS)
        self.enemy_sprite_pos = list(ENEMY_SPRITE_POS)

        # Créer les widgets UI (positions originales)
        self.hp_bar_p1 = HPBar(
            PLAYER_INFO_POS[0], PLAYER_INFO_POS[1],
            250, pokemon1, show_hp_text=True
        )
        self.hp_bar_p2 = HPBar(
            ENEMY_INFO_POS[0], ENEMY_INFO_POS[1],
            250, pokemon2, show_hp_text=False  # Pas de texte HP pour l'ennemi
        )

        self.text_box = TextBox(*TEXT_BOX_RECT)
        self.move_menu = MoveMenu(*MOVE_MENU_RECT, pokemon1.moves)

        # Phase d'intro
        self.phase = PHASE_INTRO
        self.message_queue = [
            f"Un combat commence !",
            f"{pokemon2.name.upper()} sauvage apparaît !",
            f"Go, {pokemon1.name.upper()} !",
        ]
        self.current_message_index = 0
        self.text_box.set_text(self.message_queue[0])

        # Reset animations
        self.attack_animation = None
        self.shake_animation = None
        self.impact_particles = []
        self.damage_numbers = []
        self.effectiveness_flash = None

    def handle_events(self, events):
        """Gere les inputs selon la phase courante."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.phase == PHASE_INTRO:
                    self._handle_intro_input(event)
                
                elif self.phase == PHASE_CHOOSE_MOVE:
                    self._handle_move_selection(event)
                
                elif self.phase == PHASE_SHOW_RESULTS:
                    self._handle_results_input(event)
                
                elif self.phase == PHASE_GAME_OVER:
                    self._handle_game_over_input(event)

    def _handle_intro_input(self, event):
        """Avance les messages d'intro."""
        if event.key in (pygame.K_SPACE, pygame.K_RETURN):
            if not self.text_box.is_complete:
                self.text_box.skip_animation()
                return

            self.current_message_index += 1
            if self.current_message_index < len(self.message_queue):
                self.text_box.set_text(self.message_queue[self.current_message_index])
            else:
                # Fin de l'intro, commencer le combat
                self._start_player_turn()

    def _start_player_turn(self):
        """Le joueur choisit son attaque."""
        self.phase = PHASE_CHOOSE_MOVE
        self.current_player = 1  # <-- Toujours commencer par le joueur 1
        self.move_menu.moves = self.battle.pokemon1.moves
        self.move_menu.selected_index = 0
        self.move_menu.visible = True
        self.text_box.set_text(f"Que doit faire {self.battle.pokemon1.name.upper()} ?")

    def _handle_move_selection(self, event):
        """Gère la sélection de l'attaque."""
        if self.current_player == 1:
            # Joueur 1 : WASD + Espace
            if event.key in (pygame.K_w, pygame.K_UP):
                self.move_menu.navigate("up")
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.move_menu.navigate("down")
            elif event.key in (pygame.K_a, pygame.K_LEFT):
                self.move_menu.navigate("left")
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                self.move_menu.navigate("right")
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                move = self.move_menu.get_selected_move()
                if move.has_pp():
                    self.selected_move_p1 = move
                    self.move_menu.visible = False
                    
                    if self.ai:
                        # Mode PvIA : l'IA choisit automatiquement
                        self.selected_move_p2 = self.ai.choose_move(self.battle.pokemon1)
                        self._determine_turn_order()
                        self._execute_next_attack()
                    else:
                        # Mode PvP : passer au joueur 2
                        self.current_player = 2
                        self.move_menu.moves = self.battle.pokemon2.moves
                        self.move_menu.selected_index = 0
                        self.move_menu.visible = True
                        self.text_box.set_text(f"Que doit faire {self.battle.pokemon2.name.upper()} ?")
        
        elif self.current_player == 2:
            # Joueur 2 : Flèches + Entrée
            if event.key == pygame.K_UP:
                self.move_menu.navigate("up")
            elif event.key == pygame.K_DOWN:
                self.move_menu.navigate("down")
            elif event.key == pygame.K_LEFT:
                self.move_menu.navigate("left")
            elif event.key == pygame.K_RIGHT:
                self.move_menu.navigate("right")
            elif event.key == pygame.K_RETURN:
                move = self.move_menu.get_selected_move()
                if move.has_pp():
                    self.selected_move_p2 = move
                    self.move_menu.visible = False
                    self._determine_turn_order()
                    self._execute_next_attack()

    def _determine_turn_order(self):
        """Détermine qui attaque en premier selon la vitesse."""
        p1 = self.battle.pokemon1
        p2 = self.battle.pokemon2
        
        speed1 = p1.get_effective_speed()
        speed2 = p2.get_effective_speed()
        
        if speed1 > speed2:
            self.turn_order = [
                (p1, self.selected_move_p1, True),   # (pokemon, move, is_player)
                (p2, self.selected_move_p2, False)
            ]
        elif speed2 > speed1:
            self.turn_order = [
                (p2, self.selected_move_p2, False),
                (p1, self.selected_move_p1, True)
            ]
        else:
            # Vitesse égale, aléatoire
            import random
            if random.random() < 0.5:
                self.turn_order = [
                    (p1, self.selected_move_p1, True),
                    (p2, self.selected_move_p2, False)
                ]
            else:
                self.turn_order = [
                    (p2, self.selected_move_p2, False),
                    (p1, self.selected_move_p1, True)
                ]
        
        self.current_turn_index = 0

    def _execute_next_attack(self):
        """Lance l'attaque suivante dans l'ordre."""
        if self.current_turn_index >= len(self.turn_order):
            # Les deux Pokemon ont attaqué -> fin du tour
            self._end_turn()
            return
        
        attacker, move, is_player = self.turn_order[self.current_turn_index]
        
        # Vérifier si l'attaquant est KO
        if attacker.is_fainted():
            self.current_turn_index += 1
            self._execute_next_attack()
            return
        
        # Définir attaquant et défenseur
        if is_player:
            self.current_attacker = "player"
        else:
            self.current_attacker = "enemy"
        
        # Message d'attaque
        self.text_box.set_text(f"{attacker.name.upper()} utilise {move.display_name.upper()} !")
        
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

    def _handle_results_input(self, event):
        """Avance dans les messages de résultats."""
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
                    # Combat terminé
                    self.phase = PHASE_GAME_OVER
                    self.text_box.set_text("Appuyez sur Entrée pour continuer...")
                else:
                    # Passer à l'attaque suivante ou nouveau tour
                    self.current_turn_index += 1
                    self._execute_next_attack()

    def _handle_game_over_input(self, event):
        """Gère la fin du combat."""
        if event.key == pygame.K_RETURN:
            self.state_manager.shared_data["winner"] = self.battle.winner
            self.state_manager.shared_data["loser"] = self.battle.loser
            self.state_manager.change_state("result")

    def _end_turn(self):
        """Termine le tour et vérifie les effets de statut."""
        messages = []
        
        # Effets de fin de tour (poison, brûlure)
        for pokemon in [self.battle.pokemon1, self.battle.pokemon2]:
            if pokemon.status and pokemon.status.is_active:
                msg = pokemon.status.on_turn_end(pokemon)
                if msg:
                    messages.append(msg)
                if not pokemon.status.is_active:
                    pokemon.status = None
                
                # Vérifier KO après dégâts de statut
                if pokemon.is_fainted():
                    other = self.battle.pokemon2 if pokemon == self.battle.pokemon1 else self.battle.pokemon1
                    self.battle.is_over = True
                    self.battle.winner = other
                    self.battle.loser = pokemon
                    messages.append(f"{pokemon.name.upper()} est K.O. !")
                    messages.append(f"{other.name.upper()} remporte le combat !")
                    break
        
        if self.battle.is_over:
            self.phase = PHASE_GAME_OVER
            self.message_queue = messages
            self.current_message_index = 0
            if messages:
                self.text_box.set_text(messages[0])
            self.phase = PHASE_SHOW_RESULTS
        else:
            # Nouveau tour
            if messages:
                self.message_queue = messages
                self.current_message_index = 0
                self.text_box.set_text(messages[0])
                self.phase = PHASE_SHOW_RESULTS
            else:
                self._start_player_turn()

    def update(self, dt):
        """Met a jour les animations."""
        self.text_box.update(dt)
        self.hp_bar_p1.update(dt)
        self.hp_bar_p2.update(dt)
        
        # Animations d'attaque
        if self.phase == PHASE_EXECUTE_ANIMATION:
            all_animations_done = True
            
            # Attack animation
            if self.attack_animation:
                self.attack_animation.update(dt)
                
                # Mettre à jour la position de l'attaquant
                if self.current_attacker == "player":
                    self.player_sprite_pos = list(self.attack_animation.get_attacker_position())
                else:
                    self.enemy_sprite_pos = list(self.attack_animation.get_attacker_position())
                
                # Déclencher l'impact
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
                    # Remettre la position correcte
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
            
            # Dégâts flottants
            for dmg_num in self.damage_numbers[:]:
                dmg_num.update(dt)
                if dmg_num.is_complete:
                    self.damage_numbers.remove(dmg_num)
            if self.damage_numbers:
                all_animations_done = False
            
            # Flash d'efficacité
            if self.effectiveness_flash:
                self.effectiveness_flash.update(dt)
                if self.effectiveness_flash.is_complete:
                    self.effectiveness_flash = None
                else:
                    all_animations_done = False
            
            # Toutes les animations sont terminées -> passer aux résultats
            if all_animations_done:
                self._show_attack_results()

    def _apply_attack_damage(self):
        """Applique les dégâts et lance les animations d'impact."""
        attacker, move, is_player = self.turn_order[self.current_turn_index]
        defender = self.battle.pokemon2 if is_player else self.battle.pokemon1
        
        # Vérifier la précision
        import random
        if random.randint(1, 100) > move.accuracy:
            # Attaque ratée - pas d'animation d'impact
            self._attack_missed = True
            return
        
        self._attack_missed = False
        
        # Calculer les dégâts
        if move.is_damaging():
            result = self.battle.damage_calc.calculate(attacker, defender, move)
            defender.take_damage(result.damage)
            
            # Sauvegarder le résultat pour les messages
            self._last_result = result
            
            # Position du défenseur pour les animations
            if is_player:
                defender_pos = list(ENEMY_SPRITE_POS)
            else:
                defender_pos = list(PLAYER_SPRITE_POS)
            
            # Shake
            self.shake_animation = ShakeAnimation(
                tuple(defender_pos),
                intensity=12 if result.damage > 50 else 8
            )
            
            # Particules
            particle_pos = (
                defender_pos[0] + 40,
                defender_pos[1] + 40
            )
            
            # Couleur selon efficacité
            if result.effectiveness >= 2.0:
                particle_color = (100, 255, 100)
            elif result.effectiveness < 1.0 and result.effectiveness > 0:
                particle_color = (255, 100, 100)
            else:
                particle_color = (255, 255, 100)
            
            self.impact_particles.append(ImpactParticles(particle_pos, particle_color))
            
            # Dégâts flottants
            dmg_pos = (particle_pos[0], particle_pos[1] - 20)
            self.damage_numbers.append(
                DamageNumber(
                    result.damage,
                    dmg_pos,
                    is_critical=result.is_critical,
                    is_effective=result.effectiveness
                )
            )
            
            # Flash d'efficacité
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
        """Affiche les messages de résultat de l'attaque."""
        attacker, move, is_player = self.turn_order[self.current_turn_index]
        defender = self.battle.pokemon2 if is_player else self.battle.pokemon1
        
        messages = []
        
        # Attaque ratée ?
        if hasattr(self, '_attack_missed') and self._attack_missed:
            messages.append(f"L'attaque de {attacker.name.upper()} a échoué !")
        elif hasattr(self, '_last_result') and self._last_result:
            result = self._last_result
            
            if result.effectiveness == 0:
                messages.append("Ça n'a aucun effet...")
            else:
                messages.append(f"{defender.name.upper()} perd {result.damage} PV !")
                
                # Message d'efficacité
                eff_text = self.type_chart.get_effectiveness_text(result.effectiveness)
                if eff_text:
                    messages.append(eff_text)
                
                if result.is_critical:
                    messages.append("Coup critique !")
        
        # Vérifier KO
        if defender.is_fainted():
            self.battle.is_over = True
            self.battle.winner = attacker
            self.battle.loser = defender
            messages.append(f"{defender.name.upper()} est K.O. !")
            messages.append(f"{attacker.name.upper()} remporte le combat !")
        
        # Afficher les messages
        if messages:
            self.message_queue = messages
            self.current_message_index = 0
            self.text_box.set_text(messages[0])
            self.phase = PHASE_SHOW_RESULTS
        else:
            # Pas de messages, passer au tour suivant
            self.current_turn_index += 1
            self._execute_next_attack()

    def draw(self, surface):
        """Dessine l'ecran de combat complet."""
        # Fond
        self._draw_background(surface)

        # Sprites des Pokemon
        if self.player_sprite:
            surface.blit(self.player_sprite, self.player_sprite_pos)
        if self.enemy_sprite:
            surface.blit(self.enemy_sprite, self.enemy_sprite_pos)

        # Barres de vie
        self.hp_bar_p1.draw(surface)
        self.hp_bar_p2.draw(surface)

        # Particules d'impact
        for particles in self.impact_particles:
            particles.draw(surface)
        
        # Dégâts flottants
        for dmg_num in self.damage_numbers:
            dmg_num.draw(surface)

        # Zone de texte
        self.text_box.draw(surface)
        
        # Menu des moves
        if self.move_menu.visible:
            self.move_menu.draw(surface)
        
        # Flash d'efficacité
        if self.effectiveness_flash:
            self.effectiveness_flash.draw(surface)

    def _draw_background(self, surface):
        """Dessine le fond de l'arene."""
        if self.background_image:
            surface.blit(self.background_image, (0, 0))
        else:
            # Fallback
            surface.fill((136, 192, 240))
            pygame.draw.ellipse(surface, (144, 200, 120), (420, 230, 320, 60))
            pygame.draw.ellipse(surface, (120, 176, 100), (420, 230, 320, 60), 2)
            pygame.draw.ellipse(surface, (144, 200, 120), (20, 420, 350, 70))
            pygame.draw.ellipse(surface, (120, 176, 100), (20, 420, 350, 70), 2)
            pygame.draw.rect(surface, (120, 176, 100), (0, 430, SCREEN_WIDTH, 170))