"""Classe abstraite de base pour les etats du jeu."""


class State:
    """Classe de base pour tous les etats (ecrans) du jeu."""

    def __init__(self, state_manager):
        self.state_manager = state_manager

    def enter(self):
        """Appele quand cet etat devient actif."""
        pass

    def exit(self):
        """Appele quand on quitte cet etat."""
        pass

    def handle_events(self, events):
        """Traite les evenements Pygame."""
        raise NotImplementedError

    def update(self, dt):
        """Met a jour la logique. dt = delta time en secondes."""
        raise NotImplementedError

    def draw(self, surface):
        """Dessine cet etat a l'ecran."""
        raise NotImplementedError
