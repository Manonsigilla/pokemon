"""Mixin d'animations pour l'ecran de combat."""

from battle.animation import AttackAnimation
from config import PLAYER_SPRITE_POS, ENEMY_SPRITE_POS

from states.battle.constants import PHASE_EXECUTE_ANIMATION


class BattleAnimation:
    """Methodes d'animation du combat."""

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
