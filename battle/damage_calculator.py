"""Calculateur de degats utilisant la formule Generation III."""

import random


class DamageResult:
    """Resultat d'un calcul de degats."""

    def __init__(self, damage, effectiveness, is_critical, is_stab, move):
        self.damage = damage
        self.effectiveness = effectiveness
        self.is_critical = is_critical
        self.is_stab = is_stab
        self.move = move


class DamageCalculator:
    """Calcule les degats selon la formule Gen III."""

    def __init__(self, type_chart):
        self.type_chart = type_chart

    def calculate(self, attacker, defender, move):
        """Calcule les degats d'une attaque.

        Formule : ((2*level/5+2) * power * A/D) / 50 + 2) * modifier
        modifier = STAB * type_effectiveness * random(0.85, 1.0) * critical
        """
        if not move.is_damaging():
            return DamageResult(0, 1.0, False, False, move)

        level = attacker.level
        power = move.power
        atk = attacker.get_effective_attack(move.category)
        dfn = defender.get_effective_defense(move.category)

        # Formule de base
        base = ((2 * level / 5 + 2) * power * atk / max(1, dfn)) / 50 + 2

        # Modificateurs
        stab = self._get_stab(attacker, move)
        effectiveness = self._get_type_effectiveness(move, defender)
        critical_mult, is_crit = self._get_critical()
        random_factor = self._get_random_factor()

        modifier = stab * effectiveness * critical_mult * random_factor
        damage = int(base * modifier)

        # Immunite = 0 degats
        if effectiveness == 0:
            damage = 0
        else:
            damage = max(1, damage)  # Minimum 1 degat

        return DamageResult(damage, effectiveness, is_crit, stab > 1.0, move)

    def _get_stab(self, attacker, move):
        """Same Type Attack Bonus : 1.5 si le type du move correspond au Pokemon."""
        if move.move_type in attacker.types:
            return 1.5
        return 1.0

    def _get_type_effectiveness(self, move, defender):
        """Multiplicateur d'efficacite contre les types du defenseur."""
        return self.type_chart.get_effectiveness(move.move_type, defender.types)

    def _get_critical(self):
        """Coup critique : 1/16 de chance, multiplicateur x2."""
        if random.random() < 1 / 16:
            return 2.0, True
        return 1.0, False

    def _get_random_factor(self):
        """Facteur aleatoire entre 0.85 et 1.0."""
        return random.uniform(0.85, 1.0)
