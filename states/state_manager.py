"""Gestionnaire d'etats du jeu (State Machine)."""


class StateManager:
    """Gere les transitions entre les differents etats du jeu."""

    def __init__(self):
        self.states = {}
        self.current_state = None
        self.shared_data = {}  # Donnees partagees entre etats

    def register_state(self, name, state):
        """Enregistre un etat avec un nom."""
        self.states[name] = state

    def change_state(self, name):
        """Transition vers un nouvel etat."""
        if self.current_state:
            self.current_state.exit()
        self.current_state = self.states[name]
        self.current_state.enter()

    def handle_events(self, events):
        """Delegue au state courant."""
        if self.current_state:
            self.current_state.handle_events(events)

    def update(self, dt):
        """Delegue au state courant."""
        if self.current_state:
            self.current_state.update(dt)

    def draw(self, surface):
        """Delegue au state courant."""
        if self.current_state:
            self.current_state.draw(surface)
