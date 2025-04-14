"""
this handles all the audio stuff:
- plays sound effects and background music
- manages volume settings
- supports multiple audio formats
"""
import os
import pygame
from typing import Dict, Optional, Union

class AudioManager:
    # Sound file mappings
    SOUNDS = {
        'move': 'move.wav',
        'capture': 'capture.wav',
        'check': 'check.wav',
        'game_start': 'game_start.wav',
        'game_end': 'game_end.wav'
    }
    
    def __init__(self, sound_dir: str = "assets/sounds/") -> None:
        """sets up the audio manager and loads sound files."""
        # Initialize sound mixer if not already done
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        # Set default volume
        self.volume = 0.7
        pygame.mixer.music.set_volume(self.volume)
        
        # Load sound effects
        self.sounds: Dict[str, Optional[pygame.mixer.Sound]] = {}
        self._load_sounds(sound_dir)
    
    def _load_sounds(self, sound_dir: str) -> None:
        """
        Load sound effects from files
        
        Args:
            sound_dir: Directory containing sound files
        """
        # Define supported file extensions to try
        extensions = ['.wav', '.mp3', '.ogg']
        
        for key, filename in self.SOUNDS.items():
            sound_loaded = False
            
            # Try each extension
            for ext in extensions:
                # Try with the original filename first
                if os.path.exists(os.path.join(sound_dir, filename)):
                    file_path = os.path.join(sound_dir, filename)
                    sound_loaded = self._load_sound_file(key, file_path)
                    if sound_loaded:
                        break
                
                # Try with the base name and this extension
                base_name = os.path.splitext(filename)[0]
                file_path = os.path.join(sound_dir, f"{base_name}{ext}")
                
                if os.path.exists(file_path):
                    sound_loaded = self._load_sound_file(key, file_path)
                    if sound_loaded:
                        break
            
            if not sound_loaded:
                print(f"Sound file not found for '{key}' in {sound_dir}")
                self.sounds[key] = None
    
    def _load_sound_file(self, key: str, file_path: str) -> bool:
        """
        Load a single sound file
        
        Args:
            key: Sound key
            file_path: Path to sound file
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            self.sounds[key] = pygame.mixer.Sound(file_path)
            self.sounds[key].set_volume(self.volume)
            print(f"Loaded sound: {key} from {file_path}")
            return True
        except Exception as e:
            print(f"Could not load sound {file_path}: {e}")
            self.sounds[key] = None
            return False
    
    def play(self, sound_type: str) -> None:
        """plays a specific sound effect."""
        if sound_type in self.sounds and self.sounds[sound_type]:
            self.sounds[sound_type].play()
    
    def set_volume(self, volume: float) -> None:
        """adjusts the volume for all sounds and music."""
        # Ensure volume is in valid range
        self.volume = max(0.0, min(1.0, volume))
        
        # Apply to all loaded sounds
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(self.volume)
        
        # Also set music volume (for background music if used)
        pygame.mixer.music.set_volume(self.volume)
    
    def mute(self) -> None:
        """Mute all sounds"""
        self._previous_volume = self.volume
        self.set_volume(0.0)
    
    def unmute(self) -> None:
        """Restore previous volume level"""
        if hasattr(self, '_previous_volume'):
            self.set_volume(self._previous_volume)
        else:
            self.set_volume(0.7)  # Default value
    
    def play_music(self, music_file: str, loops: int = -1) -> None:
        """starts playing background music from the given file."""
        if os.path.exists(music_file):
            try:
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.play(loops)
            except Exception as e:
                print(f"Could not play music {music_file}: {e}")
    
    def stop_music(self) -> None:
        """stops the currently playing background music."""
        pygame.mixer.music.stop()
    
    def pause_music(self) -> None:
        """Pause currently playing background music"""
        pygame.mixer.music.pause()
    
    def unpause_music(self) -> None:
        """Resume paused background music"""
        pygame.mixer.music.unpause()