import requests
import json
import time

def fetch_all_pokemon(limit=151):
    """Récupère les données de tous les Pokémon (par défaut les 151 premiers)"""
    pokemon_list = []
    
    # 1. Récupérer la liste de tous les Pokémon
    url = f"https://pokeapi.co/api/v2/pokemon?limit={limit}&offset=0"
    response = requests.get(url)
    data = response.json()
    
    for i, poke in enumerate(data["results"]):
        print(f"Récupération de {poke['name']}... ({i+1}/{limit})")
        
        # 2. Récupérer les détails de chaque Pokémon
        poke_data = requests.get(poke["url"]).json()
        
        pokemon = {
            "id": poke_data["id"],
            "name": poke_data["name"],
            "types": [t["type"]["name"] for t in poke_data["types"]],
            "stats": {
                "hp": next(s["base_stat"] for s in poke_data["stats"] if s["stat"]["name"] == "hp"),
                "attack": next(s["base_stat"] for s in poke_data["stats"] if s["stat"]["name"] == "attack"),
                "defense": next(s["base_stat"] for s in poke_data["stats"] if s["stat"]["name"] == "defense"),
                "special-attack": next(s["base_stat"] for s in poke_data["stats"] if s["stat"]["name"] == "special-attack"),
                "special-defense": next(s["base_stat"] for s in poke_data["stats"] if s["stat"]["name"] == "special-defense"),
                "speed": next(s["base_stat"] for s in poke_data["stats"] if s["stat"]["name"] == "speed"),
            },
            "sprites": {
                "front_default": poke_data["sprites"]["front_default"],
                "back_default": poke_data["sprites"]["back_default"],
                "front_shiny": poke_data["sprites"]["front_shiny"],
                "official_artwork": poke_data["sprites"]["other"]["official-artwork"]["front_default"],
            },
            "moves": [m["move"]["name"] for m in poke_data["moves"][:4]],  # Les 4 premières attaques
            "weight": poke_data["weight"],
            "height": poke_data["height"],
        }
        
        pokemon_list.append(pokemon)
        time.sleep(0.5)  # Pause pour ne pas surcharger l'API
    
    return pokemon_list


def save_to_json(data, filename="pokemon.json"):
    """Sauvegarde les données dans un fichier JSON"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"✅ {len(data)} Pokémon sauvegardés dans {filename}")


if __name__ == "__main__":
    pokemons = fetch_all_pokemon(limit=151)  # Change le limit pour plus de Pokémon
    save_to_json(pokemons)