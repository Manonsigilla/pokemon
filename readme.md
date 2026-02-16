# Pokemon Battle Arena

Jeu de combat Pokemon en Python avec Pygame, utilisant la PokeAPI pour les donnees des 151 Pokemon de la Generation 1.

## Lancer le jeu

```bash
cd pokemon
python main.py
```

**Dependances :** `pygame`, `requests`

```bash
pip install pygame requests
```

## Fonctionnalites

### Modes de jeu
- **Joueur vs Joueur** : deux joueurs sur le meme ecran
- **Joueur vs IA** : combat contre une IA avec 3 niveaux de difficulte

### Selection d'equipe
- Choisissez jusqu'a 6 Pokemon parmi les 151 disponibles
- Interface style Pokedex avec cartes retournables (stats au dos)
- Scroll pour parcourir tous les Pokemon
- En mode IA, l'adversaire compose automatiquement une equipe de meme taille

### Systeme de combat
- Attaques basees sur les vrais stats et types Pokemon
- Calcul de degats fidele aux jeux originaux (STAB, faiblesses, resistances)
- Switch de Pokemon en cours de combat
- Option de fuite
- 5 arenes aleatoires avec decors differents

### IA a 3 niveaux de difficulte

| Niveau | Attaque | Switch apres KO | Switch volontaire |
|--------|---------|-----------------|-------------------|
| **Facile** | 40% meilleur move, 60% aleatoire | Aleatoire | Non |
| **Normal** | 70% meilleur move, 30% aleatoire | Meilleur matchup de type | Non |
| **Difficile** | 100% meilleur move | Meilleur matchup de type | Oui (si desavantage de type) |

L'IA en mode Difficile peut switcher volontairement si :
- Le Pokemon actuel est desavantage en type
- Un autre Pokemon de l'equipe a un meilleur matchup
- Le Pokemon actuel a encore plus de 25% HP

### Systeme audio

Le jeu integre un systeme de son complet (`ui/sound_manager.py`) :

- **Musique** : theme Pokemon sur l'ecran titre (fichier `assets/Sons/pokemontheme.mp3`)
- **Effets sonores** : generes synthetiquement si aucun fichier `.wav` n'est present dans `assets/Sons/`
  - Selection / validation de menus
  - Coup standard, coup critique
  - Super efficace, pas tres efficace
  - KO d'un Pokemon
  - Switch de Pokemon
  - Fuite du combat
  - Victoire

Pour utiliser vos propres sons, placez des fichiers `.wav` dans `assets/Sons/` avec les noms : `hit.wav`, `super_effective.wav`, `not_effective.wav`, `ko.wav`, `select.wav`, `switch.wav`, `critical.wav`, `victory.wav`, `flee.wav`.

## Structure du projet

```
pokemon/
  main.py                  # Point d'entree
  config.py                # Constantes globales
  bdd/
    pokemon.json           # Base de donnees des 151 Pokemon (noms francais)
  api/
    api_client.py          # Client PokeAPI avec cache local
  models/
    pokemon.py             # Modele Pokemon
    player.py              # Modele Joueur (humain ou IA)
    move.py                # Modele Attaque
    type_chart.py          # Table des types (faiblesses/resistances)
  battle/
    ai.py                  # IA adversaire (3 niveaux de difficulte)
    battle.py              # Moteur de combat
    damage_calculator.py   # Calcul des degats
  states/
    state.py               # Classe abstraite State
    state_manager.py        # Gestionnaire d'etats
    title_state.py          # Menu principal
    selection_state.py      # Selection d'equipe
    battle_state.py         # Ecran de combat
    result_state.py         # Ecran de victoire
  ui/
    button.py              # Widget bouton
    pokemon_card.py        # Carte Pokemon (selection)
    pokemon_info.py        # Panneau info combat
    hp_bar.py              # Barre de PV
    text_box.py            # Boite de dialogue
    sprite_loader.py       # Chargement des sprites
    sound_manager.py       # Gestionnaire audio (musique + SFX)
  assets/
    fonts/                 # Police Pokemon custom
    Sons/                  # Musique et effets sonores
  images/                  # Fonds d'arenes
  cache/                   # Cache des sprites telecharges
```

## Changelog

### Nettoyage
- Suppression de 194 fichiers dupliques (suffixe " 2") generes accidentellement

### Noms francais
- Remplacement des 151 noms anglais par les noms francais dans `bdd/pokemon.json`

### Niveaux de difficulte IA
- Refonte de `battle/ai.py` avec 3 niveaux : facile, normal, difficile
- Ajout d'un sous-menu de difficulte dans `title_state.py`
- L'IA en mode difficile peut switcher volontairement de Pokemon
- Nom du dresseur IA adapte : Debutant / Champion / Maitre

### Systeme audio
- Creation de `ui/sound_manager.py` avec generation synthetique de sons
- Integration dans tous les ecrans : titre, selection, combat, victoire
- Support de fichiers audio personnalises (`.wav` et `.mp3`)
