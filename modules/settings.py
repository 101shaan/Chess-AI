"""
Settings manager for Chess AI:
- Theme management
- Audio settings
- Game preferences
"""
import os
import json
from typing import Dict, Any, Optional, List

# Available theme names
THEME_DEFAULT = "default"
THEME_WOODEN = "wooden"
THEME_DARK = "dark"
THEME_ROYAL = "royal"
THEME_MOONLIGHT = "moonlight"

# Define themes with their color schemes
THEMES = {
    THEME_DEFAULT: {
        "light_square": (240, 217, 181),
        "dark_square": (181, 136, 99),
        "background": (40, 44, 52),
        "text": (220, 220, 220),
        "highlight": (255, 255, 100, 120),
        "move_indicator": (255, 255, 0, 120),
        "check_indicator": (255, 0, 0, 100),
        "button": (60, 66, 80),
        "button_hover": (80, 86, 100),
        "light_gray": (100, 100, 100)
    },
    THEME_WOODEN: {
        "light_square": (240, 217, 181),
        "dark_square": (133, 94, 66),
        "background": (110, 80, 60),
        "text": (240, 230, 210),
        "highlight": (255, 255, 100, 120),
        "move_indicator": (255, 255, 0, 120),
        "check_indicator": (255, 0, 0, 100),
        "button": (90, 70, 55),
        "button_hover": (120, 90, 70),
        "light_gray": (150, 120, 100)
    },
    THEME_DARK: {
        "light_square": (100, 100, 100),
        "dark_square": (60, 60, 60),
        "background": (30, 30, 30),
        "text": (200, 200, 200),
        "highlight": (180, 180, 120, 120),
        "move_indicator": (180, 180, 0, 120),
        "check_indicator": (200, 50, 50, 100),
        "button": (50, 50, 50),
        "button_hover": (70, 70, 70),
        "light_gray": (80, 80, 80)
    },
    THEME_ROYAL: {
        "light_square": (225, 200, 170),
        "dark_square": (150, 40, 40),
        "background": (60, 10, 10),
        "text": (240, 220, 190),
        "highlight": (255, 255, 150, 120),
        "move_indicator": (255, 255, 100, 120),
        "check_indicator": (255, 50, 50, 100),
        "button": (100, 30, 30),
        "button_hover": (130, 40, 40),
        "light_gray": (120, 60, 60)
    },
    THEME_MOONLIGHT: {
        "light_square": (220, 230, 240),
        "dark_square": (70, 90, 120),
        "background": (30, 40, 60),
        "text": (220, 230, 240),
        "highlight": (180, 200, 255, 120),
        "move_indicator": (160, 200, 255, 120),
        "check_indicator": (255, 100, 100, 100),
        "button": (50, 60, 80),
        "button_hover": (70, 80, 100),
        "light_gray": (100, 110, 130)
    }
}

class SettingsManager:
    """Manages application settings and preferences"""
    
    def __init__(self, settings_file: str = "settings.json") -> None:
        """
        Initialize settings manager
        
        Args:
            settings_file: Path to settings file
        """
        self.settings_file = settings_file
        self.settings = self._load_settings()
        
        # Initialize with defaults if not loaded
        if not self.settings:
            self.settings = {
                "theme": THEME_DEFAULT,
                "music_enabled": True,
                "current_music": "background_music1.mp3",
                "volume": 0.7
            }
            self.save()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
        
        return {}
    
    def save(self) -> bool:
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get_theme(self) -> str:
        """Get current theme name"""
        return self.settings.get("theme", THEME_DEFAULT)
    
    def set_theme(self, theme: str) -> None:
        """Set theme by name"""
        if theme in THEMES:
            self.settings["theme"] = theme
            self.save()
    
    def get_theme_colors(self) -> Dict[str, Any]:
        """Get colors for current theme"""
        theme_name = self.get_theme()
        return THEMES.get(theme_name, THEMES[THEME_DEFAULT])
    
    def is_music_enabled(self) -> bool:
        """Check if background music is enabled"""
        return self.settings.get("music_enabled", True)
    
    def set_music_enabled(self, enabled: bool) -> None:
        """Set background music enabled/disabled"""
        self.settings["music_enabled"] = enabled
        self.save()
    
    def get_current_music(self) -> str:
        """Get current music file"""
        return self.settings.get("current_music", "background_music1.mp3")
    
    def set_current_music(self, music_file: str) -> None:
        """Set current music file"""
        self.settings["current_music"] = music_file
        self.save()
    
    def get_volume(self) -> float:
        """Get volume level"""
        return self.settings.get("volume", 0.7)
    
    def set_volume(self, volume: float) -> None:
        """Set volume level"""
        self.settings["volume"] = max(0.0, min(1.0, volume))
        self.save()
    
    def get_available_music(self, music_dir: str = "assets/sounds/background_music") -> List[str]:
        """Get list of available music files"""
        music_files = []
        if os.path.exists(music_dir):
            for file in os.listdir(music_dir):
                if file.endswith((".mp3", ".wav", ".ogg")):
                    music_files.append(file)
        return music_files
