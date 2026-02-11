"""Effets de statut Pokemon avec heritage de classes."""

import random


class StatusEffect:
    """Classe de base pour tous les effets de statut."""

    def __init__(self, name):
        self.name = name
        self.is_active = True

    def on_turn_start(self, pokemon):
        """Appele au debut du tour. Retourne (peut_agir, message)."""
        return True, ""

    def on_turn_end(self, pokemon):
        """Appele en fin de tour. Retourne un message de degats/effet."""
        return ""

    def __str__(self):
        return self.name.upper()


class Burn(StatusEffect):
    """Brulure : 1/16 HP max par tour, divise l'Attaque physique par 2."""

    def __init__(self):
        super().__init__("burn")

    def on_turn_end(self, pokemon):
        damage = max(1, pokemon.max_hp // 16)
        pokemon.take_damage(damage)
        return f"{pokemon.name} souffre de sa brulure ! (-{damage} PV)"


class Paralysis(StatusEffect):
    """Paralysie : 25% de chance de ne pas agir, Vitesse /2."""

    def __init__(self):
        super().__init__("paralysis")

    def on_turn_start(self, pokemon):
        if random.random() < 0.25:
            return False, f"{pokemon.name} est paralyse ! Il ne peut pas attaquer !"
        return True, ""


class Poison(StatusEffect):
    """Poison : 1/8 HP max par tour."""

    def __init__(self):
        super().__init__("poison")

    def on_turn_end(self, pokemon):
        damage = max(1, pokemon.max_hp // 8)
        pokemon.take_damage(damage)
        return f"{pokemon.name} souffre du poison ! (-{damage} PV)"


class Sleep(StatusEffect):
    """Sommeil : ne peut pas agir pendant 1 a 3 tours."""

    def __init__(self):
        super().__init__("sleep")
        self.turns_remaining = random.randint(1, 3)

    def on_turn_start(self, pokemon):
        if self.turns_remaining <= 0:
            self.is_active = False
            return True, f"{pokemon.name} se reveille !"
        self.turns_remaining -= 1
        return False, f"{pokemon.name} dort profondement..."


class Freeze(StatusEffect):
    """Gel : ne peut pas agir, 20% de chance de degeler chaque tour."""

    def __init__(self):
        super().__init__("freeze")

    def on_turn_start(self, pokemon):
        if random.random() < 0.20:
            self.is_active = False
            return True, f"{pokemon.name} a degele !"
        return False, f"{pokemon.name} est gele !"


# Dictionnaire de creation des effets de statut
STATUS_FACTORY = {
    "burn": Burn,
    "paralysis": Paralysis,
    "poison": Poison,
    "sleep": Sleep,
    "freeze": Freeze,
}
