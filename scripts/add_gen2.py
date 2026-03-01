import json

pokemon_file = "bdd/pokemon.json"

with open(pokemon_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Define the new missing Gen 2 pokemon
new_mons = [
    {
        "id": 161,
        "name": "fouinette",
        "types": ["normal"],
        "stats": {"hp": 35, "attack": 46, "defense": 34, "special-attack": 35, "special-defense": 45, "speed": 20},
        "sprites": {
            "front_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/161.png",
            "back_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/161.png",
            "front_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/161.png",
            "official_artwork": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/161.png"
        },
        "moves": ["scratch", "defense-curl", "quick-attack", "fury-swipes"],
        "weight": 60, "height": 8
    },
    {
        "id": 162,
        "name": "fouinar",
        "types": ["normal"],
        "stats": {"hp": 85, "attack": 76, "defense": 64, "special-attack": 45, "special-defense": 55, "speed": 90},
        "sprites": {
            "front_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/162.png",
            "back_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/162.png",
            "front_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/162.png",
            "official_artwork": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/162.png"
        },
        "moves": ["scratch", "defense-curl", "quick-attack", "fury-swipes"],
        "weight": 325, "height": 18
    },
    {
        "id": 163,
        "name": "hoothoot",
        "types": ["normal", "flying"],
        "stats": {"hp": 60, "attack": 30, "defense": 30, "special-attack": 36, "special-defense": 56, "speed": 50},
        "sprites": {
            "front_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/163.png",
            "back_default": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/163.png",
            "front_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/163.png",
            "official_artwork": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/163.png"
        },
        "moves": ["tackle", "growl", "foresight", "peck"],
        "weight": 212, "height": 7
    }
]

# Check if they exist to avoid duplicates
existing_names = [p["name"] for p in data]
for mon in new_mons:
    if mon["name"] not in existing_names:
        data.append(mon)
        print(f"Added {mon['name']}")

with open(pokemon_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
