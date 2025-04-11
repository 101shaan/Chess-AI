"""
UI components for online multiplayer chess.
Includes matchmaking screen, chat interface, and multiplayer-specific UI elements.
"""
import pygame
import time
import math
from typing import Dict, List, Optional, Any, Tuple, Callable

# Import from other modules
from modules.ui import Button, COLOR_BUTTON, COLOR_BUTTON_HOVER, COLOR_TEXT, COLOR_BACKGROUND, COLOR_LIGHT_GRAY
from modules.ui import WINDOW_WIDTH, WINDOW_HEIGHT, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL

# Multiplayer UI constants
CHAT_WIDTH = 250
CHAT_HEIGHT = 200
CHAT_MESSAGE_HEIGHT = 20
MAX_VISIBLE_MESSAGES = 8

class ChatBox:
    """Chat interface for multiplayer games"""
    
    def __init__(self, x: int, y: int, width: int = CHAT_WIDTH, height: int = CHAT_HEIGHT):
        self.rect = pygame.Rect(x, y, width, height)
        self.messages: List[Dict[str, str]] = []
        self.input_rect = pygame.Rect(x, y + height - 30, width - 70, 25)
        self.send_button = Button(
            x + width - 65, 
            y + height - 30, 
            60, 
            25, 
            "Send", 
            font_size=FONT_SIZE_SMALL
        )
        self.input_text = ""
        self.active = False
        self.font = pygame.font.SysFont("Arial", FONT_SIZE_SMALL)
        self.scroll_offset = 0
        self.max_scroll = 0
        self.on_send: Optional[Callable[[str], None]] = None
        self.hide_chat = False
        self.toggle_button = Button(
            x + width - 30,
            y - 30,
            30,
            25,
            "▼", 
            font_size=FONT_SIZE_SMALL
        )
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle chat box events
        
        Returns:
            True if event was handled by the chat box
        """
        # Toggle chat visibility
        if event.type == pygame.MOUSEBUTTONDOWN and self.toggle_button.is_clicked(event.pos):
            self.hide_chat = not self.hide_chat
            self.toggle_button.update_text("▼" if self.hide_chat else "▲")
            return True
            
        if self.hide_chat:
            return False
            
        # Check if user clicked inside the input box
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.input_rect.collidepoint(event.pos):
                self.active = True
                return True
            else:
                self.active = False
                
            # Check if send button was clicked
            if self.send_button.is_clicked(event.pos):
                self._send_message()
                return True
                
            # Handle scroll wheel for chat history
            if self.rect.collidepoint(event.pos):
                if event.button == 4:  # Scroll up
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                    return True
                elif event.button == 5:  # Scroll down
                    self.scroll_offset = min(self.max_scroll, self.scroll_offset + 1)
                    return True
        
        # Handle text input if box is active
        if self.active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self._send_message()
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                    return True
                elif event.key == pygame.K_ESCAPE:
                    self.active = False
                    return True
                else:
                    # Limit text length to prevent overflow
                    if len(self.input_text) < 50:
                        self.input_text += event.unicode
                    return True
        
        return False
    
    def _send_message(self):
        """Send the current message"""
        if self.input_text.strip() and self.on_send:
            # Check for special username change command
            if self.input_text.startswith("/name "):
                new_name = self.input_text[6:].strip()  # Extract the new name
                if new_name:
                    # Add a system message indicating name change
                    self.messages.append({
                        "sender": "System",
                        "message": f"You changed your name to '{new_name}'"
                    })
                    # Return special command for name change
                    self.on_send(f"__name_change__{new_name}")
                    self.input_text = ""
                    return
            # Normal message
            self.on_send(self.input_text)
            self.input_text = ""
    
    def update(self, mouse_pos: Tuple[int, int]):
        """Update chat box state"""
        if not self.hide_chat:
            self.send_button.update(mouse_pos)
        self.toggle_button.update(mouse_pos)
    
    def set_messages(self, messages: List[Dict[str, str]]):
        """Set chat messages"""
        self.messages = messages
        self.max_scroll = max(0, len(self.messages) - MAX_VISIBLE_MESSAGES)
        # Auto-scroll to bottom if already at bottom
        if self.scroll_offset == self.max_scroll - 1 or self.scroll_offset == self.max_scroll:
            self.scroll_offset = self.max_scroll
    
    def draw(self, surface: pygame.Surface):
        """Draw chat box on surface"""
        # Always draw toggle button
        self.toggle_button.draw(surface)
        
        if self.hide_chat:
            return
            
        # Draw chat box background
        pygame.draw.rect(surface, (30, 30, 30), self.rect)
        pygame.draw.rect(surface, (60, 60, 60), self.rect, 1)
        
        # Draw messages
        visible_messages = self.messages[max(0, len(self.messages) - MAX_VISIBLE_MESSAGES - self.scroll_offset):
                                        len(self.messages) - self.scroll_offset]
        
        for i, message in enumerate(visible_messages):
            y_pos = self.rect.y + 5 + i * CHAT_MESSAGE_HEIGHT
            
            # Draw sender name
            sender_text = self.font.render(f"{message['sender']}: ", True, (180, 180, 220))
            surface.blit(sender_text, (self.rect.x + 5, y_pos))
            
            # Draw message text
            message_text = self.font.render(message['message'], True, COLOR_TEXT)
            surface.blit(message_text, (self.rect.x + 5 + sender_text.get_width(), y_pos))
        
        # Draw input box
        input_box_color = (60, 60, 100) if self.active else (40, 40, 60)
        pygame.draw.rect(surface, input_box_color, self.input_rect)
        pygame.draw.rect(surface, (100, 100, 130), self.input_rect, 1)
        
        # Draw input text
        input_surface = self.font.render(self.input_text, True, COLOR_TEXT)
        surface.blit(input_surface, (self.input_rect.x + 5, self.input_rect.y + 5))
        
        # Draw send button
        self.send_button.draw(surface)
        
        # Draw scroll indicators if needed
        if self.max_scroll > 0:
            pygame.draw.polygon(
                surface, 
                (200, 200, 200) if self.scroll_offset > 0 else (100, 100, 100),
                [(self.rect.right - 15, self.rect.y + 10), 
                 (self.rect.right - 5, self.rect.y + 10), 
                 (self.rect.right - 10, self.rect.y + 5)]
            )
            pygame.draw.polygon(
                surface, 
                (200, 200, 200) if self.scroll_offset < self.max_scroll else (100, 100, 100),
                [(self.rect.right - 15, self.rect.y + CHAT_HEIGHT - 40), 
                 (self.rect.right - 5, self.rect.y + CHAT_HEIGHT - 40), 
                 (self.rect.right - 10, self.rect.y + CHAT_HEIGHT - 35)]
            )

class MatchmakingScreen:
    """Matchmaking screen UI for finding online opponents"""
    
    def __init__(self):
        self.font_large = pygame.font.SysFont("Arial", FONT_SIZE_LARGE)
        self.font_medium = pygame.font.SysFont("Arial", FONT_SIZE_MEDIUM)
        self.font_small = pygame.font.SysFont("Arial", FONT_SIZE_SMALL)
        
        # Create buttons
        self.back_button = Button(20, 20, 100, 40, "Back", font_size=FONT_SIZE_SMALL)
        
        # Player name input
        self.name_input_rect = pygame.Rect(WINDOW_WIDTH // 2 - 100, 200, 200, 30)
        self.name_input_active = False
        self.player_name = "Player"
        
        # Find game button
        self.find_game_button = Button(
            WINDOW_WIDTH // 2 - 100,
            250,
            200,
            40,
            "Find Game",
            font_size=FONT_SIZE_MEDIUM
        )
        
        # Animation variables
        self.searching = False
        self.search_start_time = 0
        self.connecting = False
        
    def handle_event(self, event: pygame.event.Event) -> Dict[str, Any]:
        """
        Handle matchmaking screen events
        
        Returns:
            Dict with action information or empty dict if no action
        """
        result = {}
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if back button was clicked
            if self.back_button.is_clicked(event.pos):
                result = {"action": "back"}
            
            # Check if name input was clicked
            elif self.name_input_rect.collidepoint(event.pos):
                self.name_input_active = True
            else:
                self.name_input_active = False
            
            # Check if find game button was clicked
            if self.find_game_button.is_clicked(event.pos) and not self.searching:
                self.searching = True
                self.search_start_time = time.time()
                result = {"action": "find_game", "player_name": self.player_name}
        
        # Handle text input for name if active
        if self.name_input_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.name_input_active = False
            elif event.key == pygame.K_BACKSPACE:
                self.player_name = self.player_name[:-1]
            else:
                # Limit name length
                if len(self.player_name) < 15:
                    self.player_name += event.unicode
        
        return result
    
    def update(self, mouse_pos: Tuple[int, int]):
        """Update matchmaking screen state"""
        self.back_button.update(mouse_pos)
        self.find_game_button.update(mouse_pos)
    
    def draw(self, surface: pygame.Surface):
        """Draw matchmaking screen"""
        # Draw background
        surface.fill(COLOR_BACKGROUND)
        
        # Draw title
        title_text = self.font_large.render("Online Multiplayer", True, COLOR_TEXT)
        surface.blit(title_text, (WINDOW_WIDTH // 2 - title_text.get_width() // 2, 80))
        
        # Draw player name label
        name_label = self.font_medium.render("Your Name:", True, COLOR_TEXT)
        surface.blit(name_label, (WINDOW_WIDTH // 2 - name_label.get_width() // 2, 170))
        
        # Draw name input box
        name_input_color = (60, 60, 100) if self.name_input_active else (40, 40, 60)
        pygame.draw.rect(surface, name_input_color, self.name_input_rect)
        pygame.draw.rect(surface, (100, 100, 130), self.name_input_rect, 1)
        
        # Draw player name text
        name_text = self.font_medium.render(self.player_name, True, COLOR_TEXT)
        surface.blit(name_text, (self.name_input_rect.x + 5, self.name_input_rect.y + 5))
        
        # Draw find game button if not searching
        if not self.searching:
            self.find_game_button.draw(surface)
        else:
            # Draw searching animation
            self.draw_searching_animation(surface)
        
        # Draw back button
        self.back_button.draw(surface)
    
    def draw_searching_animation(self, surface: pygame.Surface):
        """Draw the searching for opponent animation"""
        # Draw "Searching for opponent" text
        searching_text = self.font_medium.render("Searching for opponent...", True, COLOR_TEXT)
        surface.blit(searching_text, (WINDOW_WIDTH // 2 - searching_text.get_width() // 2, 250))
        
        # Draw animated dots
        dots = "." * (1 + int((time.time() - self.search_start_time) * 2) % 3)
        dots_text = self.font_medium.render(dots, True, COLOR_TEXT)
        surface.blit(dots_text, (WINDOW_WIDTH // 2 + searching_text.get_width() // 2, 250))
        
        # Draw spinning chess piece
        self.draw_spinning_piece(surface, WINDOW_WIDTH // 2, 330)
        
    def draw_spinning_piece(self, surface: pygame.Surface, x: int, y: int):
        """Draw spinning knight chess piece animation"""
        # Calculate rotation based on time
        angle = (time.time() - self.search_start_time) * 180 % 360
        
        # Draw the knight shape
        radius = 30
        color = (220, 220, 220)
        
        # Draw a circular base
        pygame.draw.circle(surface, (80, 80, 80), (x, y), radius)
        
        # Calculate knight points based on angle
        knight_points = []
        for i in range(8):
            point_angle = angle + i * 45
            point_x = x + int(math.cos(math.radians(point_angle)) * radius * 0.8)
            point_y = y + int(math.sin(math.radians(point_angle)) * radius * 0.8)
            knight_points.append((point_x, point_y))
        
        # Draw knight silhouette
        pygame.draw.polygon(surface, color, knight_points)
        pygame.draw.circle(surface, color, (x, y), radius // 2)
        
    def set_searching(self, searching: bool):
        """Set searching state"""
        if searching and not self.searching:
            self.search_start_time = time.time()
        self.searching = searching
        
    def reset(self):
        """Reset screen state"""
        self.searching = False
        self.name_input_active = False
