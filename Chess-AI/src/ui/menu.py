class MenuUI:
    def __init__(self, screen, settings):
        self.screen = screen
        self.settings = settings
        self.menu_options = ["New Game", "Multiplayer", "Settings", "Quit"]
        self.selected_option = 0

    def draw(self):
        self.screen.fill(self.settings.get_background_color())
        for index, option in enumerate(self.menu_options):
            color = self.settings.get_highlight_color() if index == self.selected_option else self.settings.get_text_color()
            self.draw_text(option, color, index)

    def draw_text(self, text, color, index):
        font = self.settings.get_font()
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(self.screen.get_width() // 2, 100 + index * 50))
        self.screen.blit(text_surface, text_rect)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.menu_options)
            elif event.key == pygame.K_RETURN:
                return self.select_option()

    def select_option(self):
        if self.selected_option == 0:
            return "new_game"
        elif self.selected_option == 1:
            return "multiplayer"
        elif self.selected_option == 2:
            return "settings"
        elif self.selected_option == 3:
            return "quit"
        return None