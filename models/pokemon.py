"""Classe Pokemon representant un Pokemon avec ses stats, moves et statut."""

from models.status_effect import STATUS_FACTORY


class Pokemon:
    """Represente un Pokemon avec toutes ses caracteristiques de combat."""

    def __init__(self, pokemon_id, name, level, types, base_stats, moves,
                 front_sprite_path, back_sprite_path):
        self.pokemon_id = pokemon_id
        self.name = name.title()
        self.level = level
        self.types = types  # ["fire"] ou ["grass", "poison"]

        # Stats de base (depuis l'API)
        self.base_stats = base_stats

        # Stats calculees
        self.max_hp = self._calc_hp(base_stats["hp"], level)
        self.current_hp = self.max_hp
        self.attack = self._calc_stat(base_stats["attack"], level)
        self.defense = self._calc_stat(base_stats["defense"], level)
        self.sp_attack = self._calc_stat(base_stats["special-attack"], level)
        self.sp_defense = self._calc_stat(base_stats["special-defense"], level)
        self.speed = self._calc_stat(base_stats["speed"], level)

        # Attaques (liste de Move, max 4)
        self.moves = moves

        # Statut actif (None ou StatusEffect)
        self.status = None

        # Chemins des sprites
        self.front_sprite_path = front_sprite_path
        self.back_sprite_path = back_sprite_path

    @staticmethod
    def _calc_hp(base, level):
        """HP = ((2 * base * level) / 100) + level + 10"""
        return int((2 * base * level) / 100) + level + 10

    @staticmethod
    def _calc_stat(base, level):
        """Stat = ((2 * base * level) / 100) + 5"""
        return int((2 * base * level) / 100) + 5

    def is_fainted(self):
        """Verifie si le Pokemon est KO."""
        return self.current_hp <= 0

    def take_damage(self, amount):
        """Inflige des degats au Pokemon."""
        self.current_hp = max(0, self.current_hp - amount)

    def heal(self, amount):
        """Soigne le Pokemon."""
        self.current_hp = min(self.max_hp, self.current_hp + amount)

    def apply_status(self, status_name):
        """Applique un effet de statut. Retourne un message."""
        if self.status is not None:
            return f"{self.name} a deja un probleme de statut !"
        if status_name in STATUS_FACTORY:
            self.status = STATUS_FACTORY[status_name]()
            status_messages = {
                "burn": f"{self.name} est brule !",
                "paralysis": f"{self.name} est paralyse !",
                "poison": f"{self.name} est empoisonne !",
                "sleep": f"{self.name} s'est endormi !",
                "freeze": f"{self.name} est gele !",
            }
            return status_messages.get(status_name, "")
        return ""

    def get_effective_speed(self):
        """Retourne la vitesse effective (reduite si paralyse)."""
        speed = self.speed
        if self.status and self.status.name == "paralysis":
            speed //= 2
        return speed

    def get_effective_attack(self, category):
        """Retourne l'attaque effective selon la categorie du move."""
        if category == "physical":
            atk = self.attack
            if self.status and self.status.name == "burn":
                atk //= 2
            return atk
        return self.sp_attack

    def get_effective_defense(self, category):
        """Retourne la defense effective selon la categorie du move."""
        if category == "physical":
            return self.defense
        return self.sp_defense

    def hp_percentage(self):
        """Retourne le pourcentage de HP restants (0.0 a 1.0)."""
        if self.max_hp == 0:
            return 0.0
        return self.current_hp / self.max_hp

    def __str__(self):
        types_str = "/".join(t.title() for t in self.types)
        return f"{self.name} (Nv.{self.level}) [{types_str}] PV: {self.current_hp}/{self.max_hp}"
