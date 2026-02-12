"""Système d'objets et d'inventaire."""


class Item:
    """Objet utilisable avec un effet."""

    def __init__(self, name, description, category, effect_value=0, price=0):
        self.name = name
        self.description = description
        self.category = category  # "heal", "pokeball", "status", "battle"
        self.effect_value = effect_value
        self.price = price


class Bag:
    """Inventaire du dresseur organisé par catégorie."""

    def __init__(self):
        self.items = {}  # {item_name: {"item": Item, "quantity": int}}

    def add_item(self, item, quantity=1):
        if item.name in self.items:
            self.items[item.name]["quantity"] += quantity
        else:
            self.items[item.name] = {"item": item, "quantity": quantity}

    def use_item(self, item_name, target_pokemon):
        """Utilise un objet. Retourne (succès, message)."""
        if item_name not in self.items or self.items[item_name]["quantity"] <= 0:
            return False, "Aucun objet disponible !"

        item = self.items[item_name]["item"]
        self.items[item_name]["quantity"] -= 1

        if self.items[item_name]["quantity"] <= 0:
            del self.items[item_name]

        if item.category == "heal":
            target_pokemon.heal(item.effect_value)
            return True, f"{target_pokemon.name} récupère {item.effect_value} PV !"
        elif item.category == "status":
            target_pokemon.status = None
            return True, f"{target_pokemon.name} est guéri de son statut !"

        return False, ""

    def get_items_by_category(self, category):
        return {k: v for k, v in self.items.items() if v["item"].category == category}


# Objets prédéfinis (à enrichir)
ITEMS_DATABASE = {
    "potion": Item("Potion", "Restaure 20 PV", "heal", 20, 200),
    "super-potion": Item("Super Potion", "Restaure 50 PV", "heal", 50, 700),
    "hyper-potion": Item("Hyper Potion", "Restaure 200 PV", "heal", 200, 1200),
    "antidote": Item("Antidote", "Soigne le poison", "status", 0, 100),
    "pokeball": Item("Poké Ball", "Capture un Pokémon sauvage", "pokeball", 1, 200),
    "superball": Item("Super Ball", "Meilleur taux de capture", "pokeball", 1.5, 600),
    "hyperball": Item("Hyper Ball", "Excellent taux de capture", "pokeball", 2, 1200),
}