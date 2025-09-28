import asyncio, pygame, random, time, math, sys, platform

from src.util import load_image, load_sound, load_tile_imgs, load_animation, load_palette
from src.tiles import TileMap
from src.player import Player
from src.smoke import *

# conor was here
pygame.init()
pygame.mixer.init()

# ----------- GLOBALS ----------- #
# check if python is running through emscripten
WEB_PLATFORM = sys.platform == "emscripten"
if WEB_PLATFORM:
    # for document/canvas interaction
    import js # type: ignore
    # keep pixelated look for pygbag
    platform.window.canvas.style.imageRendering = "pixelated"

WIDTH, HEIGHT = 640, 480
SCALE = 2

MAP = "data/maps/0.json"

pygame.mixer.music.load("data/audio/chicken.ogg")

# annelies was here
class App:
    def __init__(self):
        # no need for separate scaling, pygbag scales canvas automatically
        self.display = pygame.display.set_mode((WIDTH, HEIGHT), flags=pygame.RESIZABLE)
        self.screen = pygame.Surface((WIDTH // SCALE, HEIGHT // SCALE))
        self.active = True # if tab is focused when running through web

        self.clock = pygame.time.Clock()
        # delta time
        self.dt = 1
        self.last_time = time.time() - 1/60

        # sfx & image assets
        self.assets = {
            # tiles
            "tiles/grass": load_tile_imgs("tiles/cloud_tuft.png", 8),
            "tiles/cloud": load_tile_imgs("tiles/cloud.png", 8),
            "tiles/rock": load_tile_imgs("tiles/rock.png", 8),
            "tiles/moss": load_tile_imgs("tiles/moss.png", 8),
            "tiles/portal": load_animation("tiles/portal_spritesheet.png", (8, 16), 4),
            # Nathan was here
            # sfx
            "sfx/jump": load_sound("sfx/jump.ogg"),
            "sfx/falling": load_sound("sfx/falling.ogg"),
            "sfx/portal": load_sound("sfx/portal.ogg"),
            "sfx/raining": load_sound("sfx/raining.ogg"),
            "sfx/explosion": load_sound("sfx/vanish.ogg"),
            "sfx/start": load_sound("sfx/start.ogg"),
            # player
            "player/idle": load_animation("player/idle.png", [5, 8], 5),
            "player/run": load_animation("player/run.png", [5, 8], 4),
            "player/jump": load_animation("player/jump.png", [5, 8], 4),
            "player/land": load_animation("player/land.png", [5, 8], 5),
            # bg
            "backdrop": load_image("tiles/background.png"),
            "tiles/large_decor": load_animation("tiles/Cloud_large_decor.png", [50, 50], 6),
            "clouds_single": load_image("tiles/clouds_single.png"),
            # particles
            "fire": load_animation("flame.png", [5, 5], 9)
        }
        self.kickup_palette = load_palette(self.assets["tiles/cloud"][0])

        self.tile_map = TileMap(self)
        self.tile_map.load(MAP)

        self.scroll = pygame.Vector2(0, 0)
        self.screen_shake = 0

        self.tile_map = TileMap(self)
        self.tile_map.load(MAP)

        self.scroll = pygame.Vector2(0, 0)
        self.screen_shake = 0
        
        self.large_font = pygame.font.Font("data/fonts/PixelOperator8-Bold.ttf", 11)
        self.small_font = pygame.font.Font("data/fonts/PixelOperator8-Bold.ttf", 6)
        self.game_over_message = random.randint(0, 4)
        self.state = "menu"
        
        # Portal transition system
        self.transition_state = "none"  
        self.transition_timer = 0.0
        self.transition_duration = 0.2  # Half second for each fade - simple and fast
        self.next_level = None
        self.current_level = 0
        self.max_levels = 5  # Number avl lvl (Jens told me to not comment alot, so I use abbrivations :) )
        
        # Fall detection threshold
        self.fall_threshold = 600  # If player falls below this Y position, restart

        self.player = Player(self, [5, 8], [50, -10])
        
        # Initialize floating clouds system
        self.floating_clouds = []
        self.init_floating_clouds()
        
        # Timer and level tracking
        self.game_start_time = 0
        self.game_running = False
        self.total_pause_time = 0
        self.level_start_time = 0
        self.level_times = []  # Store individual level completion times
        self.show_lap_view = True  # Toggle for lap view display - on by default
        self.isFirstInput = True
        self.final_time = 0  # Store completion time for end screen
        self.end_screen_bg = None  # Store frozen game state for end screen background
        self.capture_next_frame = False  # Flag to capture screen after rendering
        self.end_screen_transition_timer = 0.0  # Timer for end screen transition
        self.end_screen_transition_duration = 1.5  # Duration of transition in seconds
        
        # Pause system
        self.game_paused = False
        self.pause_start_time = 0
        
        # Long press reset confirmation
        self.reset_key_pressed = False
        self.reset_key_start_time = 0
        self.reset_hold_duration = 1.0  # Hold for 1 second to confirm reset

        #menu loading
        self.prompt = self.large_font.render("Press ENTER to start", True, (255, 255, 255))
        self.logo_text = self.large_font.render("System of a Cloud", True, (255, 255, 255))
        self.logo = pygame.transform.scale((pygame.image.load("data/images/tiles/penguin_arm.png")), (78, 120))
        self.kickup = []
        self.sparks = []
        self.smoke = []
        self.fire = []
        
        # Start menu variables
        self.menu_title = self.large_font.render("System of a Cloud", True, (255, 255, 255))
        
        self.menu_buttons = [
            {"text": "Play", "rect": None, "action": "play"},
            {"text": "Credits", "rect": None, "action": "credits"}
        ]
        self.selected_button = 0
        self.menu_keybinds = [
            "WASD/Arrows: Move   Space/Up: Jump   P: Pause",
            "R: Reset Position   L: Toggle Times   ESC: Quit"
        ]
    
    def update_fire(self, render_scroll):
        # [pos, frame]
        for i, f in sorted(enumerate(self.fire), reverse=True):
            f[0][1] -= 2 * self.dt;
            f[1] += 0.5 * self.dt
            if f[1] >= len(self.assets['fire']):
                self.fire.pop(i)
            else:
                self.screen.blit(self.assets['fire'][math.floor(f[1])], (f[0][0] - render_scroll[0] - 2.5, f[0][1] - render_scroll[1] - 2.5))

    def update_kickup(self, render_scroll):
        # particle: [pos, vel, size, color]
        for i, p in sorted(enumerate(self.kickup), reverse=True):
            p[0][0] += p[1][0] * self.dt
            if self.tile_map.solid_check(p[0]):
                p[1][0] *= -0.8
                p[1][1] *= 0.999

            p[1][1] += 0.1 * self.dt
            p[0][1] += p[1][1] * self.dt
            if self.tile_map.solid_check(p[0]):
                p[1][1] *= -0.8
                p[1][0] *= 0.999

            p[2] -= 0.1 * self.dt
            if p[2] <= 0:
                self.kickup.pop(i)
            else:
                color = pygame.Color(p[3][0], p[3][1], p[3][2], int(p[2] / 10 * 255))
                self.screen.set_at((int(p[0][0] - render_scroll[0]), int(p[0][1] - render_scroll[1])), color)

    def update_sparks(self, render_scroll):
        for i, spark in sorted(enumerate(self.sparks), reverse=True):
            spark.update(self.dt)
            if spark.speed >= 0:
                spark.draw(self.screen, render_scroll)
            else:
                self.sparks.pop(i)

    def menu(self):
        # Draw backdrop background instead of black fill
        self.screen.blit(pygame.transform.scale(self.assets['backdrop'], self.screen.get_size()), (0, 0))
        
        # Ensure logo is initialized when entering the menu
        if not hasattr(self, 'logo') or self.logo is None:
            self.logo = pygame.transform.scale((pygame.image.load("data/images/tiles/penguin_arm.png")), (78, 120))
        
        # Draw title
        title_x = self.screen.get_width() // 2 - self.menu_title.get_width() // 2
        title_y = 30
        self.screen.blit(self.menu_title, (title_x, title_y))
        
        # Draw logo centered below title
        logo_x = self.screen.get_width() // 2 - self.logo.get_width() // 2
        logo_y = title_y + self.menu_title.get_height() + 8
        self.screen.blit(self.logo, (logo_x, logo_y))
        
        # Draw buttons below logo
        button_y = logo_y + self.logo.get_height() + 15
        button_spacing = 40
        
        for i, button in enumerate(self.menu_buttons):
            button_text = self.large_font.render(button["text"], True, (255, 255, 255))
            button_x = self.screen.get_width() // 2 - button_text.get_width() // 2
            button_rect = pygame.Rect(button_x - 10, button_y - 5, button_text.get_width() + 20, button_text.get_height() + 10)
            button["rect"] = button_rect
            
            # Highlight selected button
            if i == self.selected_button:
                pygame.draw.rect(self.screen, (100, 100, 100), button_rect, 2)
            
            self.screen.blit(button_text, (button_x, button_y))
            button_y += button_spacing
        
        # Draw keybinds below the buttons
        keybind_y = button_y + 20
        keybind_title = self.small_font.render("Controls:", True, (200, 200, 200))
        self.screen.blit(keybind_title, (self.screen.get_width() // 2 - keybind_title.get_width() // 2, keybind_y))
        keybind_y += 15
        
        for keybind in self.menu_keybinds:
            keybind_text = self.small_font.render(keybind, True, (255, 255, 255))
            self.screen.blit(keybind_text, (self.screen.get_width() // 2 - keybind_text.get_width() // 2, keybind_y))
            keybind_y += 12
    
    def handle_menu_input(self, event):
        """Handle input for the start menu"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            # Convert mouse position to screen coordinates
            mouse_x = (mouse_pos[0] - (self.display.get_width() - self.screen.get_width() * SCALE) // 2) // SCALE
            mouse_y = (mouse_pos[1] - (self.display.get_height() - self.screen.get_height() * SCALE) // 2) // SCALE
            
            for button in self.menu_buttons:
                if button["rect"] and button["rect"].collidepoint(mouse_x, mouse_y):
                    self.handle_menu_action(button["action"])
                    return
                    
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self.handle_menu_action(self.menu_buttons[self.selected_button]["action"])
            elif event.key == pygame.K_UP:
                self.selected_button = (self.selected_button - 1) % len(self.menu_buttons)
            elif event.key == pygame.K_DOWN:
                self.selected_button = (self.selected_button + 1) % len(self.menu_buttons)
    
    def handle_menu_action(self, action):
        """Handle menu button actions"""
        if action == "play":
            self.state = "game"
            self.restart_game()
        elif action == "credits":
            self.show_credits()
    
    def show_credits(self):
        """Show credits screen"""
        self.state = "credits"
    
    def credits_screen(self):
        """Draw the credits screen"""
        # Draw backdrop background instead of black fill
        self.screen.blit(pygame.transform.scale(self.assets['backdrop'], self.screen.get_size()), (0, 0))
        
        credits_title = self.large_font.render("Credits", True, (255, 255, 255))
        title_x = self.screen.get_width() // 2 - credits_title.get_width() // 2
        self.screen.blit(credits_title, (title_x, 60))
        
        credits_text = [
            "Game by: Jens, Nathan, Conor, Annelies",
            "",
            "Programming: Python + Pygame",
            "",
            "Press A to return to menu"
        
        ]
        
        y = 120
        for line in credits_text:
            if line:
                text = self.small_font.render(line, True, (255, 255, 255))
            else:
                text = self.small_font.render(" ", True, (255, 255, 255))
            self.screen.blit(text, (self.screen.get_width() // 2 - text.get_width() // 2, y))
            y += 15        
    
    def init_floating_clouds(self):
        """Initialize floating clouds at random positions and layers"""
        for i in range(4):  # Create 8 floating clouds
            cloud = {
                'x': random.randint(0, self.screen.get_width() + 100),
                'y': random.randint(-20, self.screen.get_height() + 50),
                'speed': random.uniform(0.1, 0.6),  # speeeeeeeeeeeeeeeed
                'layer': 'below',  # Only below layer
                'alpha': random.randint(60, 90),  # Semi-transparent
                'size': random.uniform(0.5, 1.5),  # Random size scaling
            }
            self.floating_clouds.append(cloud)
    
    def update_floating_clouds(self, dt):
        """Update floating cloud positions"""
        for cloud in self.floating_clouds:
            # Move cloud from right to left
            cloud['x'] -= cloud['speed'] * dt
            
            # Reset cloud position when it goes off screen
            if cloud['x'] < -50:
                cloud['x'] = self.screen.get_width() + random.randint(50, 150)
                cloud['y'] = random.randint(-50, self.screen.get_height() + 50)
                cloud['speed'] = random.uniform(0.1, 0.3)
                cloud['alpha'] = random.randint(100, 100)
                cloud['size'] = random.uniform(0.5, 1.5)
    
    def draw_floating_clouds(self, layer):
        """Draw floating clouds for specified layer ('below' or 'above')"""
        for cloud in self.floating_clouds:
            if cloud['layer'] == layer:
  
                cloud_img = self.assets["clouds_single"].copy()
                
                cloud_img.set_colorkey((0, 0, 0))  # Make black pixels transparent
                
                if cloud['size'] != 1.0:
                    new_size = (int(cloud_img.get_width() * cloud['size']), 
                               int(cloud_img.get_height() * cloud['size']))
                    cloud_img = pygame.transform.scale(cloud_img, new_size)
                
                cloud_img.set_alpha(cloud['alpha'])
                
                # Draw cloud (no scroll offset for background elements)
                self.screen.blit(cloud_img, (int(cloud['x']), int(cloud['y'])))
    
    
    def end_screen(self):
        """Draw the end screen with completion time and restart option"""
        # Paint the backdrop as background
        self.screen.blit(pygame.transform.scale(self.assets['backdrop'], self.screen.get_size()), (0, 0))
        
        # Update transition timer
        self.end_screen_transition_timer += self.dt / 60.0
        
        # Calculate transition progress (0 to 1)
        transition_progress = min(self.end_screen_transition_timer / self.end_screen_transition_duration, 1.0)
        
        # Add progressive overlay for better text readability
        overlay_alpha = int(transition_progress * 80)  # Fade in overlay
        if overlay_alpha > 0:
            overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(overlay_alpha)
            self.screen.blit(overlay, (0, 0))
        
        # Only show text after some transition progress
        if transition_progress > 0.2:
            text_alpha = min((transition_progress - 0.2) / 0.8, 1.0)  # Fade in text
            text_alpha_value = int(text_alpha * 255)
            
            # Title
            title_text = self.large_font.render("Game Complete!", True, (0, 255, 0))
            title_text.set_alpha(text_alpha_value)
            title_x = (self.screen.get_width() - title_text.get_width()) // 2
            self.screen.blit(title_text, (title_x, self.screen.get_height() // 4))
            
            # Final time display
            minutes = int(self.final_time // 60)
            seconds = int(self.final_time % 60)
            millis = int((self.final_time % 1) * 1000)
            time_text = f"Final Time: {minutes:02d}:{seconds:02d}:{millis:02d}"
            time_surface = self.large_font.render(time_text, True, (255, 255, 255))
            time_surface.set_alpha(text_alpha_value)
            time_x = (self.screen.get_width() - time_surface.get_width()) // 2
            self.screen.blit(time_surface, (time_x, self.screen.get_height() // 2))
            
            # Restart instruction (appears after some delay)
            if transition_progress > 0.6:
                restart_alpha = min((transition_progress - 0.6) / 0.4, 1.0)
                restart_alpha_value = int(restart_alpha * 255)
                restart_text = self.large_font.render("Press ENTER to restart", True, (255, 255, 255))
                restart_text.set_alpha(restart_alpha_value)
                restart_x = (self.screen.get_width() - restart_text.get_width()) // 2
                self.screen.blit(restart_text, (restart_x, self.screen.get_height() // 1.5))
            if transition_progress > 0.7:
                restart_alpha = min((transition_progress - 0.7) / 0.3, 1.0)
                restart_alpha_value = int(restart_alpha * 255)
                restart_text = self.large_font.render("Press ENTER to restart", True, (255, 255, 255))
                restart_text.set_alpha(restart_alpha_value)
                restart_x = (self.screen.get_width() - restart_text.get_width()) // 2
                self.screen.blit(restart_text, (restart_x, self.screen.get_height() // 1.5))
                restart_text.set_alpha(restart_alpha_value)
                restart_x = (self.screen.get_width() - restart_text.get_width()) // 2
                self.screen.blit(restart_text, (restart_x, self.screen.get_height() // 1.5))
    

    
    def capture_game_screen(self):
        """Capture screen for end screen (not used with backdrop approach)"""
        # Reset transition timer for smooth end screen transition
        self.end_screen_transition_timer = 0.0
    
    def start_level_transition(self, next_level):
        """Start the fade-out transition to a new level"""
        if self.transition_state == "none":
            self.transition_state = "fade_out"
            self.transition_timer = 0.0
            self.next_level = next_level
            # Play portal sound
            if "sfx/portal" in self.assets:
                self.assets["sfx/portal"].play()
    
    def update_transition(self, dt):
        """Update the level transition animation"""
        if self.transition_state == "none":
            return
        
        self.transition_timer += dt
        
        if self.transition_state == "fade_out":
            if self.transition_timer >= self.transition_duration:
                # Fade out complete, load new level and start fade in
                self.load_level(self.next_level)
                self.transition_state = "fade_in"
                self.transition_timer = 0.0
                
        elif self.transition_state == "fade_in":
            if self.transition_timer >= self.transition_duration:
                # Transition complete
                self.transition_state = "none"
                self.transition_timer = 0.0
                self.next_level = None
    
    def load_level(self, level_number):
        """Load a new level"""
        self.current_level = level_number
        level_file = f"data/maps/{level_number}.json"
        
        # Reset level start time for new level
        self.level_start_time = time.time()
        
        # Reset player position for new level
        self.player.pos = pygame.Vector2(50, 10)
        self.player.movement = pygame.Vector2(0, 0)
        
        # Load new level
        self.tile_map = TileMap(self)
        try:
            self.tile_map.load(level_file)
        except FileNotFoundError:
            # If level doesn't exist, wrap around to level 0
            self.current_level = 0
            self.tile_map.load("data/maps/0.json")
    
    def draw_transition_overlay(self):
        """Draw the fade overlay during transitions"""
        if self.transition_state == "none":
            return
        
        # Simple linear progress from 0 to 1
        progress = self.transition_timer / self.transition_duration
        progress = max(0.0, min(1.0, progress))
        
        alpha = 0
        if self.transition_state == "fade_out":
            # Fade to white: 0 -> 255
            alpha = int(255 * progress)
        elif self.transition_state == "fade_in":
            # Fade from white: 255 -> 0
            alpha = int(255 * (1.0 - progress))
        
        # Create and draw white overlay
        if alpha > 0:
            overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
            overlay.fill((255, 255, 255))
            overlay.set_alpha(alpha)
            self.screen.blit(overlay, (0, 0))
    

    # put all the game stuff here
    def restart_game(self):
        self.current_level = 0
        self.player.pos = pygame.Vector2(50, 10)
        self.player.movement = pygame.Vector2(0, 0)
        self.player.falling = 30
        self.transition_state = "none"
        self.transition_timer = 0.0
        self.tile_map = TileMap(self)
        self.tile_map.load("data/maps/0.json")
        self.state = "game"
        # Reset timer - wait for first input to start
        self.game_running = False
        self.game_start_time = 0
        self.level_times = []  # Reset level times
        self.total_pause_time = 0  # Reset pause time
        self.isFirstInput = True


    def reset_player_position(self):
        """Reset only the player position without changing level"""
        self.player.pos = pygame.Vector2(50, 10)
        self.player.movement = pygame.Vector2(0, 0)
        self.player.falling = 30
    
    def draw_timer(self):
        """Draw current level timer on top left"""
        if self.state == "game":
            if self.game_running and hasattr(self, 'level_start_time'):
                # Calculate current level time (excluding pause time)
                elapsed_time = time.time() - self.level_start_time - self.total_pause_time
                minutes = int(elapsed_time // 60)
                seconds = int(elapsed_time % 60)
                millis = int((elapsed_time % 1) * 1000)
                timer_text = f"{minutes:02d}:{seconds:02d}.{millis//10:02d}"

                timer_color = (60, 255, 84)  # green when timer is running
            else:
                # Show 00:00.00 when timer hasn't started yet
                timer_text = "00:00.00"
                timer_color = (157, 67, 67)  # Red when timer hasn't started
            
            timer_surface = self.small_font.render(timer_text, True, timer_color)
            self.screen.blit(timer_surface, (8, 8))  # Top left corner
    
    def draw_level_counter(self):
        """Draw level counter on top right"""
        if self.state == "game":
            level_text = f"Level: {self.current_level + 1}"  # Display as 1-based instead of 0-based
            
            level_surface = self.small_font.render(level_text, True, (255, 255, 255))
            # Position on top right
            x_pos = self.screen.get_width() - level_surface.get_width() - 8
            self.screen.blit(level_surface, (x_pos, 8))

    def update(self):
        # Always update long press reset regardless of pause state
        self.update_long_press_reset()
        
        # Always update transitions (whether paused or not)
        # Pass seconds to transition updater for consistent fade timing
        self.update_transition(self.dt / 60.0)
        
        # Skip game logic updates if paused
        if self.game_paused:
            # When paused, only do rendering updates below
            pass
        else:
            # Only update game logic if not transitioning and not paused
            if self.transition_state == "none":
                # Update tile destruction timers
                self.tile_map.update(self.dt / 60.0)  # Convert dt to seconds
                
                # Update floating clouds
                self.update_floating_clouds(self.dt)
                
                self.player.update(self.dt, self.tile_map)
                
                # Check if player has fallen too far (restart game)
                if self.player.pos.y > self.fall_threshold:
                    self.reset_player_position()
                    self.screen_shake = 5

                if self.player.pos.y > self.fall_threshold - 100:
                    if "sfx/falling" in self.assets:
                        self.assets["sfx/falling"].play()
                    return
                
                # Check for portal collision
                self.check_portal_collision()

        # Always update camera and rendering
        self.scroll.x += (self.player.pos.x - self.screen.get_width() / 2 - self.scroll.x) * 0.1 * self.dt
        self.scroll.y += (self.player.pos.y - self.screen.get_height() / 2 - self.scroll.y) * 0.05 * self.dt

        self.screen_shake = max(0, self.screen_shake - 1 * self.dt)
        screen_shake_offset = (random.random() * self.screen_shake - self.screen_shake / 2, random.random() * self.screen_shake - self.screen_shake / 2)
        render_scroll = (int(self.scroll.x + screen_shake_offset[0]), int(self.scroll.y + screen_shake_offset[1]))
        self.screen.blit(pygame.transform.scale(self.assets['backdrop'], self.screen.get_size()), (0, 0))
        
        # Draw clouds below the level (pause-aware)
        self.draw_floating_clouds('below')
        
        self.tile_map.draw(self.screen, render_scroll)

        # Only update particles if not paused
        if not self.game_paused:
            self.update_kickup(render_scroll)
            self.update_sparks(render_scroll)
            for i, bit in sorted(enumerate(self.smoke), reverse=True):
                bit.update(self.dt)
                if bit.timer > SMOKE_DELAY // FADE:
                    self.smoke.pop(i)
                bit.draw(self.screen, render_scroll)
            self.update_fire(render_scroll)
        else:
            # Draw particles without updating when paused
            for bit in self.smoke:
                bit.draw(self.screen, render_scroll)
            # Draw static fire
            for f in self.fire:
                if f[1] < len(self.assets['fire']):
                    fire_img = self.assets['fire'][int(f[1])]
                    self.screen.blit(fire_img, (f[0][0] - render_scroll[0], f[0][1] - render_scroll[1]))
            # Kickup and sparks are just dots/pixels, skip rendering when paused for simplicity

        self.player.draw(self.screen, render_scroll)
        
        # Draw transition overlay
        self.draw_transition_overlay()
        
        # Draw portal distance progress bar (only during gameplay)
        if self.state == "game" and self.transition_state == "none":
            self.draw_portal_progress_bar()
        
        # Draw level counter only (removed timer)
        if self.state == "game":
            self.draw_level_counter()
        
        # Draw lap view (contains the level timing information)
        self.draw_lap_view()
        
        # Draw pause overlay if game is paused
        if self.game_paused:
            self.draw_pause_overlay()
        
        # Draw reset progress bar if K is being held
        self.draw_reset_progress()
        
        # Capture screen if needed (after all rendering is complete)
        if hasattr(self, 'capture_next_frame') and self.capture_next_frame:
            self.capture_game_screen()
            self.capture_next_frame = False
            self.state = "end_screen"
    
    def find_portal_position(self):
        """Find the position of the portal tile in the current level"""
        for tile_loc, tile in self.tile_map.tile_map.items():
            if tile['type'] == 'portal':
                # Return the center position of the portal tile
                tile_x = tile['pos'][0] * self.tile_map.tile_size + self.tile_map.tile_size // 2
                tile_y = tile['pos'][1] * self.tile_map.tile_size + self.tile_map.tile_size // 2
                return pygame.Vector2(tile_x, tile_y)
        return None
    
    def draw_portal_progress_bar(self):
        """Draw a progress bar showing distance to portal"""
        portal_pos = self.find_portal_position()
        if portal_pos is None:
            return
        

        player_center = pygame.Vector2(self.player.pos.x + self.player.dimensions.x // 2,
                                     self.player.pos.y + self.player.dimensions.y // 2)
        distance = player_center.distance_to(portal_pos)
        
        max_distance = 1440.0 
        
        progress = max(0.0, min(1.0, 1.0 - (distance / max_distance)))
        
        # Progress bar dimensions - made smaller
        bar_width = 150  # Reduced from 150
        bar_height = 3  # Reduced from 8
        bar_x = (self.screen.get_width() - bar_width) // 2
        bar_y = 8        # Moved up slightly
        
        # Draw background bar
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2))
        pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        
        # Draw progress bar fill
        fill_width = int(bar_width * progress)
        # if progress > 0.7:
        #     # Close to portal - green
        #     color = (0, 255, 0)
        # elif progress > 0.3:
        #     # Medium distance - yellow
        #     color = (154, 167, 178)
        # else:
        #     # Far from portal - red
        #     color = (242, 167, 178)
        color = (242, 167, 178)
        
        if fill_width > 0:
            pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_width, bar_height))
        
        # Draw portal icon at the end (right side) of the progress bar using actual portal image
        portal_icon_x = bar_x + bar_width + 3
        portal_icon_y = bar_y - 3  # Adjust for image height
        if "tiles/portal" in self.assets and len(self.assets["tiles/portal"]) > 0:
            portal_img = self.assets["tiles/portal"][0]  # Get first frame of portal animation
            # Scale down the portal image to fit nicely
            portal_scaled = pygame.transform.scale(portal_img, (8, 8))
            self.screen.blit(portal_scaled, (portal_icon_x, portal_icon_y))
        
        # Draw player icon that moves with the progress using actual player image
        player_progress_x = bar_x + int(bar_width * progress) - 4  # Center the player icon on progress
        player_icon_y = bar_y - 3  # Adjust for image height
        if "player/idle" in self.assets and len(self.assets["player/idle"]) > 0:
            player_img = self.assets["player/idle"][0]  # Get first frame of player animation
            # Scale down the player image to fit nicely
            player_scaled = pygame.transform.scale(player_img, (8, 8))
            self.screen.blit(player_scaled, (player_progress_x, player_icon_y))
        
        # # Draw label text - smaller font would be nice but using existing
        # label_text = self.large_font.render("Portal", True, (255, 255, 255))  # Shortened text
        # label_x = (self.screen.get_width() - label_text.get_width()) // 2
        # self.screen.blit(label_text, (label_x, bar_y - 12))  # Adjusted spacing
    
    def check_portal_collision(self):
        """Check if player is colliding with a portal tile"""
        # Don't check for portals on the very first few frames to prevent immediate transitions
        if not hasattr(self, 'frames_since_start'):
            self.frames_since_start = 0
        self.frames_since_start += 1
        
        if self.frames_since_start < 10:  # Wait at least 10 frames before allowing transitions
            return
            
        player_rect = self.player.get_rect()
        player_center = (player_rect.centerx, player_rect.centery)
        
        # Check tiles around player for portals
        tiles_around = self.tile_map.tiles_around(player_center)
        for tile in tiles_around:
            if tile['type'] == 'portal':
                # Record current level time before transitioning
                if self.game_running and hasattr(self, 'level_start_time'):
                    current_level_time = time.time() - self.level_start_time - self.total_pause_time
                    self.level_times.append(current_level_time)
                
                # Check if this is the final level
                if self.current_level >= self.max_levels - 1:
                    # Game completed! Store final time first
                    if self.game_running:
                        self.final_time = time.time() - self.game_start_time
                        self.game_running = False
                    # Flag to capture screen at the end of update
                    self.capture_next_frame = True
                else:
                    # Player touched portal, start transition to next level
                    next_level = self.current_level + 1
                    self.start_level_transition(next_level)
    def check_if_first_input(self):
        """Check if this is the first input to start the game timer"""
        if self.isFirstInput:
            self.game_start_time = time.time()
            self.level_start_time = time.time()
            self.game_running = True
            self.isFirstInput = False
            if "sfx/start" in self.assets:
                self.assets["sfx/start"].play()

    def toggle_lap_view(self):
        """Toggle the lap view display"""
        self.show_lap_view = not self.show_lap_view
    
    def draw_lap_view(self):
        """Draw lap view as a vertical list in top left corner"""
        if not self.show_lap_view:
            return
            
        # Calculate total time
        total_time = sum(self.level_times) if self.level_times else 0
        if self.game_running and hasattr(self, 'level_start_time'):
            # Add current level time (accounting for pause state)
            if not self.game_paused:
                current_level_time = time.time() - self.level_start_time - self.total_pause_time
            else:
                # When paused, freeze the current level time calculation
                current_level_time = time.time() - self.level_start_time - self.total_pause_time - (time.time() - self.pause_start_time)
            total_time += current_level_time
        
        # Starting position in top left
        start_x = 10
        start_y = 10
        line_height = 12
        
        # Draw title
        title_text = self.small_font.render("LEVEL TIMES", True, (255, 255, 255))
        self.screen.blit(title_text, (start_x, start_y))
        y_pos = start_y + line_height + 5
        
        # Draw individual level times
        for i, level_time in enumerate(self.level_times):
            level_minutes = int(level_time // 60)
            level_seconds = int(level_time % 60)
            level_millis = int((level_time % 1) * 1000)
            
            level_text = f"L{i+1}: {level_minutes:02d}:{level_seconds:02d}.{level_millis//10:02d}"
            level_surface = self.small_font.render(level_text, True, (200, 200, 200))
            self.screen.blit(level_surface, (start_x, y_pos))
            y_pos += line_height
        
        # Show current level time if game is running and not paused
        if self.game_running and hasattr(self, 'level_start_time') and not self.game_paused:
            current_level_time = time.time() - self.level_start_time - self.total_pause_time
            current_minutes = int(current_level_time // 60)
            current_seconds = int(current_level_time % 60)
            current_millis = int((current_level_time % 1) * 1000)
            
            current_text = f"Now: {current_minutes:02d}:{current_seconds:02d}.{current_millis//10:02d}"
            current_surface = self.small_font.render(current_text, True, (100, 255, 100))
            self.screen.blit(current_surface, (start_x, y_pos))
            y_pos += line_height + 3
        elif self.game_running and hasattr(self, 'level_start_time') and self.game_paused:
            # Show paused current level time (frozen)
            current_level_time = time.time() - self.level_start_time - self.total_pause_time - (time.time() - self.pause_start_time)
            current_minutes = int(current_level_time // 60)
            current_seconds = int(current_level_time % 60)
            current_millis = int((current_level_time % 1) * 1000)
            
            current_text = f"Now: {current_minutes:02d}:{current_seconds:02d}.{current_millis//10:02d} [PAUSED]"
            current_surface = self.small_font.render(current_text, True, (255, 255, 100))
            self.screen.blit(current_surface, (start_x, y_pos))
            y_pos += line_height + 3
        
        # Draw total time if there's any time to show
        if total_time > 0:
            total_minutes = int(total_time // 60)
            total_seconds = int(total_time % 60)
            total_millis = int((total_time % 1) * 1000)
            total_text = f"Total: {total_minutes:02d}:{total_seconds:02d}.{total_millis//10:02d}"
            total_surface = self.small_font.render(total_text, True, (255, 255, 100))
            self.screen.blit(total_surface, (start_x, y_pos))

    def toggle_pause(self):
        """Toggle game pause state"""
        if self.state == "game" and self.game_running:
            if not self.game_paused:
                # Pausing the game
                self.game_paused = True
                self.pause_start_time = time.time()
            else:
                # Unpausing the game
                self.game_paused = False
                # Add the pause duration to total pause time
                if hasattr(self, 'pause_start_time'):
                    self.total_pause_time += time.time() - self.pause_start_time

    def draw_pause_overlay(self):
        """Draw pause screen overlay"""
        if not self.game_paused:
            return
            
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))
        
        # Draw pause text
        pause_text = self.large_font.render("PAUSED", True, (255, 255, 255))
        pause_x = (self.screen.get_width() - pause_text.get_width()) // 2
        pause_y = (self.screen.get_height() - pause_text.get_height()) // 2 - 20
        self.screen.blit(pause_text, (pause_x, pause_y))
        
        # Draw instructions
        instructions = [
            "P - Resume",
            "L - Toggle Level Times",
            "Hold K - Reset Game",
            "ESC - Quit"
        ]
        
        y_offset = pause_y + 40
        for instruction in instructions:
            instruction_surface = self.small_font.render(instruction, True, (200, 200, 200))
            instruction_x = (self.screen.get_width() - instruction_surface.get_width()) // 2
            self.screen.blit(instruction_surface, (instruction_x, y_offset))
            y_offset += 18

    def update_long_press_reset(self):
        """Update long press reset functionality"""
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_k]:
            if not self.reset_key_pressed:
                # Start tracking the key press
                self.reset_key_pressed = True
                self.reset_key_start_time = time.time()
            else:
                # Check if held long enough
                hold_time = time.time() - self.reset_key_start_time
                if hold_time >= self.reset_hold_duration:
                    self.restart_game()
                    self.reset_key_pressed = False
        else:
            # Key released, reset tracking
            self.reset_key_pressed = False
    
    def draw_reset_progress(self):
        """Draw reset confirmation progress bar"""
        if not self.reset_key_pressed:
            return
            
        hold_time = time.time() - self.reset_key_start_time
        progress = min(1.0, hold_time / self.reset_hold_duration)
        
        # Draw progress bar
        bar_width = 100
        bar_height = 8
        bar_x = (self.screen.get_width() - bar_width) // 2
        bar_y = self.screen.get_height() - 40
        
        # Background
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2))
        pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        
        # Progress fill
        fill_width = int(bar_width * progress)
        if fill_width > 0:
            color = (255, 100, 100) if progress < 1.0 else (100, 255, 100)
            pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_width, bar_height))
        
        # Label
        reset_text = self.small_font.render("Hold K to Reset", True, (255, 255, 255))
        reset_x = (self.screen.get_width() - reset_text.get_width()) // 2
        self.screen.blit(reset_text, (reset_x, bar_y - 20))


    # asynchronous main loop to run in browser
    async def run(self):
        pygame.mixer.music.play(-1)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.WINDOWRESIZED:
                    self.screen = pygame.Surface((self.display.get_width() // SCALE, self.display.get_height() // SCALE))
                
                # Handle menu input
                if self.state == "menu":
                    self.handle_menu_input(event)
                elif self.state == "credits":
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_a:
                        self.state = "menu"
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self.state == "end_screen":
                            self.restart_game()
                        elif self.state == "game":
                            self.restart_game()
                    # Remove immediate K key restart - now handled by long press
                    if event.key == pygame.K_p:
                        self.toggle_pause()
                    if event.key == pygame.K_r:
                        self.reset_player_position()
                    if event.key == pygame.K_l:
                        self.toggle_lap_view()
                    if event.key == pygame.K_ESCAPE:
                        print('Game Quitted')
                        return 
                    if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w or event.key == pygame.K_BACKSPACE:
                        self.player.jumping = 0
                        self.player.controls['up'] = True
                        self.check_if_first_input()
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.player.controls['down'] = True
                        self.check_if_first_input()
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.player.controls['left'] = True
                        self.check_if_first_input()
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.player.controls['right'] = True
                        self.check_if_first_input()
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w or event.key == pygame.K_BACKSPACE:
                        self.player.controls['up'] = False
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.player.controls['down'] = False
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.player.controls['left'] = False
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.player.controls['right'] = False
            
            # update delta time
            self.dt = (time.time() - self.last_time) * 60
            self.last_time = time.time()

            if self.state == "menu":
                self.menu()
            elif self.state == "game":
                # update game
                self.update()
            elif self.state == "end_screen":
                self.end_screen()
            elif self.state == "credits":
                self.credits_screen()
            # check if tab is focused if running through web (avoid messing up dt and stuff)
            if WEB_PLATFORM:
                self.active = not js.document.hidden

            # check if page is active
            if self.active:
                if WEB_PLATFORM:
                    pygame.display.set_caption(f"FPS: {self.clock.get_fps() :.1f}")
                else:
                    pygame.display.set_caption(f"FPS: {self.clock.get_fps() :.1f} Display: {self.screen.get_width()} * {self.screen.get_height()}")
                # scale display
                self.display.blit(pygame.transform.scale_by(self.screen, SCALE), (0, 0))
                pygame.display.flip()
            else:
                pygame.display.set_caption("IDLE")

            await asyncio.sleep(0) # keep this for pygbag to work
            self.clock.tick(60) # don't really need more than 60 fps

# run App() asynchronously so it works with pygbag
async def main():
    app = App()
    await app.run()

# start
asyncio.run(main())
