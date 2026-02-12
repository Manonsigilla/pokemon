import requests
import json
import time

def fetch_type_multipliers():
    """Récupère les multiplicateurs de dégâts pour les 18 types Pokémon"""
    
    # Les 18 types officiels
    types = [
        "normal", "fire", "water", "electric", "grass", "ice",
        "fighting", "poison", "ground", "flying", "psychic", "bug",
        "rock", "ghost", "dragon", "dark", "steel", "fairy"
    ]
    
    type_data = {}
    
    for t in types:
        print(f"Récupération du type {t}...")
        url = f"https://pokeapi.co/api/v2/type/{t}"
        response = requests.get(url)
        data = response.json()
        
        damage_relations = data["damage_relations"]
        
        type_data[t] = {
            "double_damage_to": [d["name"] for d in damage_relations["double_damage_to"]],      # x2
            "half_damage_to": [d["name"] for d in damage_relations["half_damage_to"]],          # x0.5
            "no_damage_to": [d["name"] for d in damage_relations["no_damage_to"]],              # x0
            "double_damage_from": [d["name"] for d in damage_relations["double_damage_from"]],  # x2 reçu
            "half_damage_from": [d["name"] for d in damage_relations["half_damage_from"]],      # x0.5 reçu
            "no_damage_from": [d["name"] for d in damage_relations["no_damage_from"]],          # x0 reçu
        }
        
        time.sleep(0.3)
    
    return type_data


def save_types(data, filename="types.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"✅ {len(data)} types sauvegardés dans {filename}")


if __name__ == "__main__":
    types = fetch_type_multipliers()
    save_types(types)