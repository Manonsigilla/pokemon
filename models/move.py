"""Classe Move representant une attaque Pokemon."""


class Move:
    """Represente une attaque Pokemon avec ses caracteristiques."""

    def __init__(self, name, power, accuracy, pp, move_type, category,
                 ailment=None, ailment_chance=0):
        self.name = name
        self.display_name = name.replace("-", " ").title()
        self.power = power
        self.accuracy = accuracy
        self.max_pp = pp
        self.current_pp = pp
        self.move_type = move_type
        self.category = category  # "physical", "special", "status"
        self.ailment = ailment  # "burn", "paralysis", "poison", "sleep", "freeze"
        self.ailment_chance = ailment_chance  # pourcentage (0-100)

    def has_pp(self):
        """Verifie si l'attaque peut encore etre utilisee."""
        return self.current_pp > 0

    def use(self):
        """Decremente les PP de 1."""
        if self.current_pp > 0:
            self.current_pp -= 1

    def is_damaging(self):
        """Retourne True si l'attaque inflige des degats."""
        return self.category in ("physical", "special") and self.power > 0

    def __str__(self):
        return f"{self.display_name} ({self.move_type.title()}, PP: {self.current_pp}/{self.max_pp})"
