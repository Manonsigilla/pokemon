import json

def load_types(filename="types.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def get_multiplier(attacker_type, defender_type, type_data):
    """
    Retourne le multiplicateur de dégâts :
    - 2.0 si super efficace
    - 0.5 si pas très efficace
    - 0.0 si aucun effet
    - 1.0 sinon (normal)
    """
    if defender_type in type_data[attacker_type]["double_damage_to"]:
        return 2.0
    elif defender_type in type_data[attacker_type]["half_damage_to"]:
        return 0.5
    elif defender_type in type_data[attacker_type]["no_damage_to"]:
        return 0.0
    else:
        return 1.0

# Exemple d'utilisation :
# type_data = load_types()
# multiplicateur = get_multiplier("fire", "grass", type_data)
# print(f"Feu vs Plante : x{multiplicateur}")  # Affiche x2.0