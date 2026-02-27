"""Client API pour Pokemon - Lit d'abord la BDD locale (bdd/), puis PokeAPI en fallback."""

import json
import os
import requests

from config import API_BASE_URL, SPRITE_URL_FRONT, SPRITE_URL_BACK, CACHE_DIR, DEFAULT_LEVEL, BASE_DIR
from api.cache import Cache
from models.move import Move
from models.pokemon import Pokemon
from models.evolution import EvolutionManager


class APIClient:
    """Recupere les donnees Pokemon depuis la BDD locale ou PokeAPI avec mise en cache."""

    def __init__(self):
        self.base_url = API_BASE_URL
        self.cache = Cache(CACHE_DIR)
        self.session = requests.Session()

        # Charger la BDD locale de Manon
        self.local_pokemon_db = self._load_local_pokemon_db()

        self.evolution_manager = EvolutionManager()

    def _load_local_pokemon_db(self):
        """Charge bdd/pokemon.json en memoire. Retourne un dict {id: pokemon_data}."""
        db_path = os.path.join(BASE_DIR, "bdd", "pokemon.json")
        if os.path.exists(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                pokemon_list = json.load(f)
            # Indexer par ID pour acces rapide
            return {p["id"]: p for p in pokemon_list}
        print("ATTENTION: bdd/pokemon.json introuvable, fallback sur API")
        return {}

    def fetch_pokemon_data(self, pokemon_id):
        """Recupere les donnees brutes d'un Pokemon (BDD locale > cache > API)."""

        # 1. Chercher dans la BDD locale de Manon
        if pokemon_id in self.local_pokemon_db:
            local = self.local_pokemon_db[pokemon_id]
            return self._convert_local_to_format(local)

        # 2. Chercher dans le cache
        cached = self.cache.get_json("pokemon", str(pokemon_id))
        if cached:
            return cached

        # 3. Fallback: appeler l'API
        url = f"{self.base_url}/pokemon/{pokemon_id}"
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        result = {
            "id": data["id"],
            "name": data["name"],
            "types": [t["type"]["name"] for t in data["types"]],
            "stats": {},
            "moves": [],
        }

        for stat in data["stats"]:
            stat_name = stat["stat"]["name"]
            result["stats"][stat_name] = stat["base_stat"]

        for move_entry in data["moves"]:
            move_name = move_entry["move"]["name"]
            for version in move_entry["version_group_details"]:
                if version["move_learn_method"]["name"] == "level-up":
                    level_learned = version["level_learned_at"]
                    result["moves"].append({
                        "name": move_name,
                        "level": level_learned,
                    })
                    break

        self.cache.save_json("pokemon", str(pokemon_id), result)
        return result

    def _convert_local_to_format(self, local_data):
        """Convertit les donnees de bdd/pokemon.json au format attendu par le gameplay."""
        return {
            "id": local_data["id"],
            "name": local_data["name"],
            "types": local_data["types"],
            "stats": {
                "hp": local_data["stats"]["hp"],
                "attack": local_data["stats"]["attack"],
                "defense": local_data["stats"]["defense"],
                "special-attack": local_data["stats"]["special-attack"],
                "special-defense": local_data["stats"]["special-defense"],
                "speed": local_data["stats"]["speed"],
            },
            "moves": [
                {"name": move_name, "level": 1}
                for move_name in local_data.get("moves", [])
            ],
        }

    def fetch_move_data(self, move_name):
        """Recupere les donnees d'une attaque (cache puis API)."""
        cached = self.cache.get_json("moves", move_name)
        if cached:
            return cached

        url = f"{self.base_url}/move/{move_name}"
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        ailment = None
        ailment_chance = 0
        if data.get("meta"):
            meta = data["meta"]
            ailment_name = meta.get("ailment", {}).get("name", "none")
            if ailment_name != "none":
                ailment = ailment_name
                ailment_chance = meta.get("ailment_chance", 0)

        result = {
            "name": data["name"],
            "power": data["power"] or 0,
            "accuracy": data["accuracy"] or 100,
            "pp": data["pp"] or 10,
            "type": data["type"]["name"],
            "category": data["damage_class"]["name"],
            "ailment": ailment,
            "ailment_chance": ailment_chance,
        }

        self.cache.save_json("moves", move_name, result)
        return result

    def download_sprite(self, pokemon_id, side="front"):
        """Telecharge un sprite et le met en cache. Retourne le chemin local."""
        cached_path = self.cache.get_sprite_path(pokemon_id, side)
        if cached_path:
            return cached_path

        if side == "front":
            url = SPRITE_URL_FRONT.format(id=pokemon_id)
        else:
            url = SPRITE_URL_BACK.format(id=pokemon_id)

        response = self.session.get(url, timeout=15)
        response.raise_for_status()

        path = self.cache.save_sprite(pokemon_id, side, response.content)
        return path

    def build_pokemon(self, pokemon_id, level=DEFAULT_LEVEL):
        """Construit un objet Pokemon complet."""
        data = self.fetch_pokemon_data(pokemon_id)
        types = data["types"]

        # Selectionner 4 moves
        selected_move_names = self._select_moves(data["moves"], types, level)

        # Recuperer les donnees de chaque move
        moves = []
        for move_name in selected_move_names:
            try:
                move_data = self.fetch_move_data(move_name)
                move = Move(
                    name=move_data["name"],
                    power=move_data["power"],
                    accuracy=move_data["accuracy"],
                    pp=move_data["pp"],
                    move_type=move_data["type"],
                    category=move_data["category"],
                    ailment=move_data.get("ailment"),
                    ailment_chance=move_data.get("ailment_chance", 0),
                )
                moves.append(move)
            except Exception:
                continue

        # S'assurer d'avoir au moins 1 move (Struggle en dernier recours)
        if not moves:
            moves.append(Move("struggle", 50, 100, 99, "normal", "physical"))

        # Completer a 4 si necessaire
        while len(moves) < 4:
            moves.append(Move("struggle", 50, 100, 99, "normal", "physical"))

        # Telecharger les sprites
        front_sprite = self.download_sprite(pokemon_id, "front")
        back_sprite = self.download_sprite(pokemon_id, "back")

        pokemon = Pokemon(
            pokemon_id=data["id"],
            name=data["name"],
            level=level,
            types=types,
            base_stats=data["stats"],
            moves=moves[:4],
            front_sprite_path=front_sprite,
            back_sprite_path=back_sprite,
        )

        return pokemon

    def get_pokemon_preview(self, pokemon_id):
        """Recupere les infos de base pour l'ecran de selection."""
        data = self.fetch_pokemon_data(pokemon_id)
        front_sprite = self.download_sprite(pokemon_id, "front")
        return {
            "id": data["id"],
            "name": data["name"].title(),
            "types": data["types"],
            "sprite_path": front_sprite,
            "stats": data["stats"],
        }

    def _select_moves(self, available_moves, pokemon_types, level):
        """Selectionne les 4 meilleures attaques pour un Pokemon."""
        # Filtrer par niveau
        eligible = [m for m in available_moves if m["level"] <= level]
        if not eligible:
            eligible = available_moves[:10] if available_moves else []

        # Recuperer les donnees de tous les moves candidats
        move_details = []
        for move_entry in eligible:
            try:
                data = self.fetch_move_data(move_entry["name"])
                if data["power"] > 0:
                    is_stab = data["type"] in pokemon_types
                    score = data["power"] * (1.5 if is_stab else 1.0)
                    move_details.append((move_entry["name"], data, score, is_stab))
            except Exception:
                continue

        # Trier par score decroissant
        move_details.sort(key=lambda x: x[2], reverse=True)

        selected = []
        selected_types = set()

        # D'abord, prendre le meilleur move STAB
        for name, data, score, is_stab in move_details:
            if is_stab and name not in selected:
                selected.append(name)
                selected_types.add(data["type"])
                break

        # Ensuite, remplir avec les meilleurs moves en variant les types
        for name, data, score, is_stab in move_details:
            if len(selected) >= 4:
                break
            if name not in selected:
                if data["type"] not in selected_types or len(selected) >= 3:
                    selected.append(name)
                    selected_types.add(data["type"])

        # Si toujours pas assez, prendre les meilleurs restants
        for name, data, score, is_stab in move_details:
            if len(selected) >= 4:
                break
            if name not in selected:
                selected.append(name)

        return selected[:4]
    
    def evolve_pokemon(self, pokemon):
        """Fait evoluer un Pokemon si possible.

        Args:
            pokemon: Objet Pokemon a faire evoluer

        Returns:
            tuple: (a_evolue: bool, message: str)
        """
        evo_id = self.evolution_manager.get_evolution_id(pokemon)
        if evo_id is None:
            return False, ""

        try:
            evo_data = self.fetch_pokemon_data(evo_id)
            front_sprite = self.download_sprite(evo_id, "front")
            back_sprite = self.download_sprite(evo_id, "back")

            message = pokemon.evolve(
                new_id=evo_data["id"],
                new_name=evo_data["name"],
                new_types=evo_data["types"],
                new_base_stats=evo_data["stats"],
                new_front_sprite=front_sprite,
                new_back_sprite=back_sprite,
            )

            return True, message

        except Exception as e:
            print(f"[Evolution] Erreur evolution: {e}")
            return False, ""