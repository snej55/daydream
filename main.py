import asyncio, pygame, random, time, math, sys, platform

from src.util import load_image, load_sound, load_tile_imgs, load_animation
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
            "tiles/portal": load_animation("tiles/portal_spritesheet.png", (8, 16), 4),
            
            
            # sfx
            "sfx/jump": load_sound("sfx/jump.ogg"),
            "sfx/falling": load_sound("sfx/falling.ogg"),
            "sfx/portal": load_sound("sfx/portal.ogg"),
            "sfx/raining": load_sound("sfx/raining.ogg"),
            "sfx/explosion": load_sound("sfx/vanish.ogg"),
            # player
            "player/idle": load_animation("player/idle.png", [5, 8], 5),
            "player/run": load_animation("player/run.png", [5, 8], 4),
            "player/jump": load_animation("player/jump.png", [5, 8], 4),
            "player/land": load_animation("player/land.png", [5, 8], 5),
            # bg
            "backdrop": load_image("tiles/background.png")
        }

        self.tile_map = TileMap(self)
        self.tile_map.load(MAP)

        self.scroll = pygame.Vector2(0, 0)
        self.screen_shake = 0

        self.tile_map = TileMap(self)
        self.tile_map.load(MAP)

        self.scroll = pygame.Vector2(0, 0)
        self.screen_shake = 0
        
        self.large_font = pygame.font.Font("data/fonts/PixelOperator8-Bold.ttf", 11)

        self.game_over_message = random.randint(0, 4)
        self.state = "menu"
        
        # Portal transition system
        self.transition_state = "none"  
        self.transition_timer = 0.0
        self.transition_duration = 0.5  # 0.7 seconds for each fade
        self.next_level = None
        self.current_level = 0
        self.max_levels = 2  # Number avl lvl (Jens told me to not comment alot, so I use abbrivations :) )
        
        # Fall detection threshold
        self.fall_threshold = 600  # If player falls below this Y position, restart

        self.player = Player(self, [5, 8], [50, -10])

        #menu loading
        self.prompt = self.large_font.render("Press ENTER to start", True, (255, 255, 255))
        self.logo_text = self.large_font.render("System of a Cloud", True, (255, 255, 255))

    def menu(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.prompt, (self.screen.get_width() // 2 - self.prompt.get_width() // 2, self.screen.get_height() // 2 - self.prompt.get_height() // 2))
        self.screen.blit(self.logo_text, (self.screen.get_width() // 2 - self.logo_text.get_width() // 2, self.screen.get_height() // 10 - self.logo_text.get_height() // 2))        
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

    def reset_player_position(self):
        """Reset only the player position without changing level"""
        self.player.pos = pygame.Vector2(50, 10)
        self.player.movement = pygame.Vector2(0, 0)
        self.player.falling = 30

    def update(self):
        # Update transitions
        self.update_transition(self.dt / 60.0)
        
        # Only update game logic if not transitioning
        if self.transition_state == "none":
            # Update tile destruction timers
            self.tile_map.update(self.dt / 60.0)  # Convert dt to seconds
            
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
        self.tile_map.draw(self.screen, render_scroll)

        self.player.draw(self.screen, render_scroll)
        
        # Draw transition overlay
        self.draw_transition_overlay()
    
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
                    if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.player.jumping = 0
                        self.player.controls['up'] = True
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.player.controls['down'] = True
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.player.controls['left'] = True
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.player.controls['right'] = True
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
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
