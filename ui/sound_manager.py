"""Gestionnaire de sons et musique pour Pokemon Battle Arena."""

import os
import pygame

from config import BASE_DIR


# Chemins des fichiers audio
SOUNDS_DIR = os.path.join(BASE_DIR, "assets", "Sons")
MUSIC_DIR = SOUNDS_DIR


class SoundManager:
    """Gere la musique de fond et les effets sonores.

    Utilise pygame.mixer pour la musique (1 piste) et les SFX (multi-pistes).
    Genere des sons synthetiques si les fichiers .wav sont absents.
    """

    def __init__(self):
        self._initialized = False
        self._music_volume = 0.4
        self._sfx_volume = 0.5
        self._sfx_cache = {}
        self._current_music = None
        self._init_mixer()

    def _init_mixer(self):
        """Initialise le mixer Pygame."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._initialized = True
        except pygame.error:
            print("SoundManager: impossible d'initialiser le mixer audio")
            self._initialized = False

    # ------------------------------------------------------------------
    # Musique de fond
    # ------------------------------------------------------------------

    def play_music(self, music_name, loops=-1, fade_ms=500):
        """Joue une musique de fond. loops=-1 pour boucle infinie."""
        if not self._initialized:
            return

        music_path = os.path.join(MUSIC_DIR, music_name)
        if not os.path.exists(music_path):
            return

        # Ne pas relancer si c'est deja la meme musique
        if self._current_music == music_path and pygame.mixer.music.get_busy():
            return

        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(self._music_volume)
            pygame.mixer.music.play(loops, fade_ms=fade_ms)
            self._current_music = music_path
        except pygame.error:
            pass

    def stop_music(self, fade_ms=500):
        """Arrete la musique avec un fondu."""
        if not self._initialized:
            return
        try:
            pygame.mixer.music.fadeout(fade_ms)
            self._current_music = None
        except pygame.error:
            pass

    def set_music_volume(self, volume):
        """Regle le volume de la musique (0.0 a 1.0)."""
        self._music_volume = max(0.0, min(1.0, volume))
        if self._initialized:
            pygame.mixer.music.set_volume(self._music_volume)

    # ------------------------------------------------------------------
    # Effets sonores synthetiques
    # ------------------------------------------------------------------

    def _generate_sfx(self, name):
        """Genere un effet sonore synthetique simple."""
        import array
        import math

        sample_rate = 44100

        if name == "hit":
            # Bruit d'impact court
            duration = 0.12
            samples = int(sample_rate * duration)
            buf = array.array("h", [0] * samples)
            for i in range(samples):
                t = i / sample_rate
                decay = max(0, 1.0 - t / duration)
                # Bruit blanc attenue + basse frequence
                noise = (hash(i) % 20000 - 10000) * decay * 0.3
                bass = math.sin(2 * math.pi * 80 * t) * 8000 * decay
                buf[i] = int(max(-32767, min(32767, noise + bass)))
            return pygame.mixer.Sound(buffer=buf)

        elif name == "super_effective":
            # Son aigu montant
            duration = 0.25
            samples = int(sample_rate * duration)
            buf = array.array("h", [0] * samples)
            for i in range(samples):
                t = i / sample_rate
                freq = 600 + t * 1200
                decay = max(0, 1.0 - t / duration)
                val = math.sin(2 * math.pi * freq * t) * 10000 * decay
                buf[i] = int(max(-32767, min(32767, val)))
            return pygame.mixer.Sound(buffer=buf)

        elif name == "not_effective":
            # Son grave descendant
            duration = 0.2
            samples = int(sample_rate * duration)
            buf = array.array("h", [0] * samples)
            for i in range(samples):
                t = i / sample_rate
                freq = 400 - t * 200
                decay = max(0, 1.0 - t / duration)
                val = math.sin(2 * math.pi * freq * t) * 8000 * decay
                buf[i] = int(max(-32767, min(32767, val)))
            return pygame.mixer.Sound(buffer=buf)

        elif name == "ko":
            # Son de KO (descente rapide)
            duration = 0.4
            samples = int(sample_rate * duration)
            buf = array.array("h", [0] * samples)
            for i in range(samples):
                t = i / sample_rate
                freq = 500 * max(0.1, 1.0 - t / duration)
                decay = max(0, 1.0 - t / duration)
                val = math.sin(2 * math.pi * freq * t) * 12000 * decay
                buf[i] = int(max(-32767, min(32767, val)))
            return pygame.mixer.Sound(buffer=buf)

        elif name == "select":
            # Bip de selection
            duration = 0.08
            samples = int(sample_rate * duration)
            buf = array.array("h", [0] * samples)
            for i in range(samples):
                t = i / sample_rate
                decay = max(0, 1.0 - t / duration)
                val = math.sin(2 * math.pi * 800 * t) * 8000 * decay
                buf[i] = int(max(-32767, min(32767, val)))
            return pygame.mixer.Sound(buffer=buf)

        elif name == "switch":
            # Son de switch Pokemon (double bip)
            duration = 0.2
            samples = int(sample_rate * duration)
            buf = array.array("h", [0] * samples)
            for i in range(samples):
                t = i / sample_rate
                decay = max(0, 1.0 - t / duration)
                freq = 600 if t < 0.1 else 900
                val = math.sin(2 * math.pi * freq * t) * 8000 * decay
                buf[i] = int(max(-32767, min(32767, val)))
            return pygame.mixer.Sound(buffer=buf)

        elif name == "critical":
            # Son de coup critique (impact + aigu)
            duration = 0.18
            samples = int(sample_rate * duration)
            buf = array.array("h", [0] * samples)
            for i in range(samples):
                t = i / sample_rate
                decay = max(0, 1.0 - t / duration)
                noise = (hash(i) % 20000 - 10000) * decay * 0.2
                tone = math.sin(2 * math.pi * 1000 * t) * 10000 * decay
                buf[i] = int(max(-32767, min(32767, noise + tone)))
            return pygame.mixer.Sound(buffer=buf)

        elif name == "victory":
            # Fanfare simple (do-mi-sol-do)
            duration = 0.8
            samples = int(sample_rate * duration)
            buf = array.array("h", [0] * samples)
            notes = [(523, 0.0, 0.18), (659, 0.2, 0.18),
                     (784, 0.4, 0.18), (1047, 0.6, 0.2)]
            for i in range(samples):
                t = i / sample_rate
                val = 0
                for freq, start, dur in notes:
                    if start <= t < start + dur:
                        note_t = t - start
                        decay = max(0, 1.0 - note_t / dur)
                        val += math.sin(2 * math.pi * freq * t) * 10000 * decay
                buf[i] = int(max(-32767, min(32767, val)))
            return pygame.mixer.Sound(buffer=buf)

        elif name == "flee":
            # Son de fuite (descente rapide)
            duration = 0.3
            samples = int(sample_rate * duration)
            buf = array.array("h", [0] * samples)
            for i in range(samples):
                t = i / sample_rate
                freq = 800 * max(0.2, 1.0 - t / duration)
                decay = max(0, 1.0 - t / duration)
                val = math.sin(2 * math.pi * freq * t) * 6000 * decay
                buf[i] = int(max(-32767, min(32767, val)))
            return pygame.mixer.Sound(buffer=buf)

        return None

    def _get_sfx(self, name):
        """Recupere un SFX depuis le cache ou le genere."""
        if name not in self._sfx_cache:
            # D'abord essayer de charger un fichier
            wav_path = os.path.join(SOUNDS_DIR, f"{name}.wav")
            if os.path.exists(wav_path):
                try:
                    self._sfx_cache[name] = pygame.mixer.Sound(wav_path)
                except pygame.error:
                    self._sfx_cache[name] = self._generate_sfx(name)
            else:
                # Generer le son synthetiquement
                self._sfx_cache[name] = self._generate_sfx(name)
        return self._sfx_cache.get(name)

    # ------------------------------------------------------------------
    # API publique pour les effets sonores
    # ------------------------------------------------------------------

    def play_sfx(self, name):
        """Joue un effet sonore par nom."""
        if not self._initialized:
            return
        sfx = self._get_sfx(name)
        if sfx:
            sfx.set_volume(self._sfx_volume)
            sfx.play()

    def play_hit(self):
        self.play_sfx("hit")

    def play_super_effective(self):
        self.play_sfx("super_effective")

    def play_not_effective(self):
        self.play_sfx("not_effective")

    def play_ko(self):
        self.play_sfx("ko")

    def play_select(self):
        self.play_sfx("select")

    def play_switch(self):
        self.play_sfx("switch")

    def play_critical(self):
        self.play_sfx("critical")

    def play_victory(self):
        self.play_sfx("victory")

    def play_flee(self):
        self.play_sfx("flee")

    def set_sfx_volume(self, volume):
        """Regle le volume des SFX (0.0 a 1.0)."""
        self._sfx_volume = max(0.0, min(1.0, volume))

    def play_battle_music(self):
        """Joue la musique de combat en arene."""
        self.play_music("battle.mp3")

# Instance globale (singleton)
sound_manager = SoundManager()
