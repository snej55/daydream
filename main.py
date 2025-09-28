import asyncio, pygame, random, time, math, sys, platform

from src.util import load_image, load_sound, load_tile_imgs, load_animation, load_palette
from src.tiles import TileMap
from src.player import Player

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
SMOKE_DELAY = 2

# annelies
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
            "tiles/grass": load_tile_imgs("tiles/grass.png", 8),
            "tiles/cloud": load_tile_imgs("tiles/cloud.png", 8),
            "tiles/rock": load_tile_imgs("tiles/rock.png", 8),
            "tiles/moss": load_tile_imgs("tiles/moss.png", 8),
            "tiles/portal": load_animation("tiles/portal_spritesheet.png", (8, 16), 4),
            
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
            "tiles/large_decor": load_animation("tiles/large_decor.png", [50, 50], 6),
            "clouds_single": load_image("tiles/clouds_single.png")
        }
        self.kickup_palette = load_palette(self.assets["tiles/cloud"][0])
        self.smoke_palette = load_palette(self.assets["tiles/rock"][0])

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
        self.transition_duration = 0.5  # 0.7 seconds for each fade
        self.next_level = None
        self.current_level = 0
        self.max_levels = 4  # Number avl lvl (Jens told me to not comment alot, so I use abbrivations :) )
        
        # Fall detection threshold
        self.fall_threshold = 600  # If player falls below this Y position, restart

        self.player = Player(self, [5, 8], [50, -10])
        
        # Initialize floating clouds system
        self.floating_clouds = []
        self.init_floating_clouds()
        
        # Timer and level tracking
        self.game_start_time = 0
        self.game_running = False
        self.isFirstInput = True

        #menu loading
        self.prompt = self.large_font.render("Press ENTER to start", True, (255, 255, 255))
        self.logo_text = self.large_font.render("System of a Cloud", True, (255, 255, 255))
        self.logo = pygame.transform.scale((pygame.image.load("data/images/tiles/penguin_arm.png")), (78, 120))
        self.kickup = []
        self.sparks = []
        self.smoke = []
    
    @staticmethod
    def alpha_surf(dim, alpha, color):
        surf = pygame.Surface(dim)
        surf.fill(color)
        surf.set_alpha(alpha)
        return surf.convert_alpha()

    def calc_smoke(self, smoke, render_scroll):
        smoke[0][0] += smoke[1][0] * self.dt
        smoke[0][1] += smoke[1][1] * self.dt
        smoke[1][0] += (smoke[1][0] * 0.98 - smoke[1][0]) * self.dt
        smoke[1][1] += (smoke[1][1] * 0.98 - smoke[1][1]) * self.dt
        smoke[4] += 5 * self.dt
        smoke[3] = max(0, smoke[3] - SMOKE_DELAY * self.dt)
        smoke[2] += 0.2 * self.dt
        surf = pygame.transform.rotate(self.alpha_surf([smoke[2], smoke[2]], smoke[3], smoke[6]), smoke[4])
        if not smoke[3]:
            self.smoke.remove(smoke)
        return (surf, (smoke[0][0] - surf.get_width() * 0.5 - render_scroll[0], smoke[0][1] - surf.get_height() * 0.5 - render_scroll[1]))

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
                self.screen.set_at((p[0][0] - render_scroll[0], p[0][1] - render_scroll[1]), color)

    def update_sparks(self, render_scroll):
        for i, spark in sorted(enumerate(self.sparks), reverse=True):
            spark.update(self.dt)
            if spark.speed >= 0:
                spark.draw(self.screen, render_scroll)
            else:
                self.sparks.pop(i)

    def menu(self):
        self.screen.fill((0, 0, 0)) 
        self.screen.blit(self.prompt, (self.screen.get_width() // 2 - self.prompt.get_width() // 2, self.screen.get_height() // 2 - self.prompt.get_height() // 2))
        self.screen.blit(self.logo_text, (self.screen.get_width() // 2 - self.logo_text.get_width() // 2, self.screen.get_height() // 10 - self.logo_text.get_height() // 2))        
    
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
    
    
        self.logo = pygame.transform.scale((pygame.image.load("data/images/tiles/penguin_arm.png")), (78, 120))

    def menu(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.prompt, (self.screen.get_width() // 2 - self.prompt.get_width() // 2, self.screen.get_height() // 1.55 - self.prompt.get_height() // 2))
        self.screen.blit(self.logo_text, (self.screen.get_width() // 2 - self.logo_text.get_width() // 2, self.screen.get_height() // 1.8 - self.logo_text.get_height() // 2))        
        self.screen.blit(self.logo, (self.screen.get_width() // 2 - self.logo.get_width() // 2, self.screen.get_height() // 3.5 - self.logo.get_height() // 2))
    
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
                # Fade out complete, load new level dand start fade in
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
        
        # Calculate fade alpha
        progress = self.transition_timer / self.transition_duration
        
        if self.transition_state == "fade_out":
            # Fade to white (ease out)
            alpha = int(255 * self.ease_out(progress))
        elif self.transition_state == "fade_in":
            # Fade from white (ease in)
            alpha = int(255 * (1 - self.ease_in(progress)))
        
        # Create fade overlay - WHITE instead of black
        fade_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        fade_surface.fill((255, 255, 255))  # White fade
        fade_surface.set_alpha(alpha)
        self.screen.blit(fade_surface, (0, 0))
    
    def ease_out(self, t):
        """Ease out function for smooth fade"""
        return 1 - (1 - t) ** 3
    
    def ease_in(self, t):
        """Ease in function for smooth fade"""
        return t ** 3
    
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
        self.isFirstInput = True


    def reset_player_position(self):
        """Reset only the player position without changing level"""
        self.player.pos = pygame.Vector2(50, 10)
        self.player.movement = pygame.Vector2(0, 0)
        self.player.falling = 30
    
    def draw_timer(self):
        """Draw game timer on top left"""
        if self.state == "game":
            if self.game_running:
                elapsed_time = time.time() - self.game_start_time
                minutes = int(elapsed_time // 60)
                seconds = int(elapsed_time % 60)
                millis = int((elapsed_time % 1) * 1000)
                timer_text = f"{minutes:02d}:{seconds:02d}:{millis:02d}"

                timer_color = (0, 255, 0)  # Green when timer is running
            else:
                # Show 00:00:00 when timer hasn't started yet
                timer_text = "00:00:000"
                timer_color = (255, 0, 0)  # Red when timer hasn't started
            
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
        # Update transitions
        self.update_transition(self.dt / 60.0)
        
        # Only update game logic if not transitioning
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
        
        # Draw clouds below the level
        self.draw_floating_clouds('below')
        
        self.tile_map.draw(self.screen, render_scroll)

        self.update_kickup(render_scroll)
        self.update_sparks(render_scroll)
        self.screen.fblits([self.calc_smoke(smoke, render_scroll) for smoke in self.smoke.copy()])

        self.player.draw(self.screen, render_scroll)
        
        # Draw transition overlay
        self.draw_transition_overlay()
        
        # Draw portal distance progress bar (only during gameplay)
        if self.state == "game" and self.transition_state == "none":
            self.draw_portal_progress_bar()
        
        # Draw timer and level counter
        if self.state == "game":
            self.draw_timer()
            self.draw_level_counter()
    
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
        bar_width = 190  # Reduced from 150
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
        player_rect = self.player.get_rect()
        player_center = (player_rect.centerx, player_rect.centery)
        
        # Check tiles around player for portals
        tiles_around = self.tile_map.tiles_around(player_center)
        for tile in tiles_around:
            if tile['type'] == 'portal':
                # Player touched portal, start transition to next level
                next_level = (self.current_level + 1) % self.max_levels
                self.start_level_transition(next_level)
    def check_if_first_input(self):
        """Check if this is the first input to start the game timer"""
        if self.isFirstInput:
            self.game_start_time = time.time()
            self.game_running = True
            self.isFirstInput = False
            if "sfx/start" in self.assets:
                self.assets["sfx/start"].play()


    # asynchronous main loop to run in browser
    async def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.WINDOWRESIZED:
                    self.screen = pygame.Surface((self.display.get_width() // SCALE, self.display.get_height() // SCALE))
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.restart_game()
                    if event.key == pygame.K_k:
                        self.restart_game()
                    if event.key == pygame.K_r:
                        self.reset_player_position()
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
            self.clock.tick(120) # don't really need more than 60 fps

# run App() asynchronously so it works with pygbag
async def main():
    app = App()
    await app.run()

# start
asyncio.run(main())
