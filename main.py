import asyncio, pygame, random, time, math, sys, platform

from src.util import load_image, load_sound, load_tile_imgs
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
            "tiles/grass": load_tile_imgs("tiles/grass.png", 8),
            "sfx/explosion": load_sound("sfx/explosion.ogg"),
            "sfx/jump": load_sound("sfx/jump.ogg"),
            "sfx/falling": load_sound("sfx/falling.ogg"),
            "sfx/portal": load_sound("sfx/portal.ogg"),
            "sfx/raining": load_sound("sfx/raining.ogg")
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

        self.player = Player(self, [7, 12], [50, 10])
    
    def menu(self):
        self.prompt_m_x = self.screen.get_width() // 2 - 100
        self.prompt_m_y = self.screen.get_height() // 2 - 50
        pygame.draw.rect(self.screen, (100, 0, 0), [self.prompt_m_x, self.prompt_m_y, 200, 100])
        self.prompt_m = self.large_font.render("Click Here", True, (255, 255, 255))
        self.screen.blit(self.prompt_m, ((self.prompt_m_x - self.prompt_m.get_width() // 2 + 100), (self.prompt_m_y + 50 - self.prompt_m.get_height() // 2)))

    def game_over(self):
        self.screen.fill((0, 0, 0))
        game_over_messages = ["Did you get that on camera?", "I'm not mad, just dissapointed", "Caught in 4K", "You did not try your best"]
        message = game_over_messages[self.game_over_message % len(game_over_messages)]
        self.prompt_go_x = self.screen.get_width() // 2 - 100
        self.prompt_go_y = self.screen.get_height() // 2 - 50
        pygame.draw.rect(self.screen, (100, 0, 0), (self.prompt_go_x, self.prompt_go_y, 200, 100))
        self.prompt_go = self.large_font.render(f"{message}", True, (255, 255, 255))
        self.prompt_go_2 = self.large_font.render("Click Here", True, (255, 255, 255))
        self.screen.blit(self.prompt_go_2, ((self.prompt_go_x - self.prompt_go_2.get_width() // 2 + 100), (self.prompt_go_y + 50 - self.prompt_go_2.get_height() // 2)))
        self.screen.blit(self.prompt_go, ((self.prompt_go_x - self.prompt_go.get_width() // 2 + 100), (self.prompt_go_y + 50 - self.prompt_go.get_height() // 2) + 75))
    
    # put all the game stuff here
    def update(self):
        # Update tile destruction timers
        self.tile_map.update(self.dt / 60.0)  # Convert dt to seconds
        
        self.player.update(self.dt, self.tile_map)

        self.scroll.x += (self.player.pos.x - self.screen.get_width() / 2 - self.scroll.x) * 0.1 * self.dt
        self.scroll.y += (self.player.pos.y - self.screen.get_height() / 2 - self.scroll.y) * 0.05 * self.dt

        self.screen_shake = max(0, self.screen_shake - 1 * self.dt)
        screen_shake_offset = (random.random() * self.screen_shake - self.screen_shake / 2, random.random() * self.screen_shake - self.screen_shake / 2)
        render_scroll = (int(self.scroll.x + screen_shake_offset[0]), int(self.scroll.y + screen_shake_offset[1]))
        self.screen.fill((0, 0, 0))
        self.tile_map.draw(self.screen, render_scroll)

        self.player.draw(self.screen, render_scroll)

    # asynchronous main loop to run in browser
    async def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.WINDOWRESIZED:
                    self.screen = pygame.Surface((self.display.get_width() // SCALE, self.display.get_height() // SCALE))
                if event.type == pygame.MOUSEBUTTONDOWN and self.state == "menu":
                    mx, my = pygame.mouse.get_pos()
                    mx //= SCALE
                    my //= SCALE
                    if self.prompt_m_x <= mx <= self.prompt_m_x + 200 and self.prompt_m_y <= my <= self.prompt_m_y + 100:
                        self.state = "game"
                if event.type == pygame.MOUSEBUTTONDOWN and self.state == "game_over":
                    mx, my = pygame.mouse.get_pos()
                    mx //= SCALE
                    my //= SCALE
                    if self.prompt_go_x <= mx <= self.prompt_go_x + 200 and self.prompt_go_y <= my <= self.prompt_go_y + 100:
                        self.state = "game"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.player.jumping = 0
                        self.player.controls['up'] = True
                    if event.key == pygame.K_DOWN:
                        self.player.controls['down'] = True
                    if event.key == pygame.K_LEFT:
                        self.player.controls['left'] = True
                    if event.key == pygame.K_RIGHT:
                        self.player.controls['right'] = True
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                        self.player.controls['up'] = False
                    if event.key == pygame.K_DOWN:
                        self.player.controls['down'] = False
                    if event.key == pygame.K_LEFT:
                        self.player.controls['left'] = False
                    if event.key == pygame.K_RIGHT:
                        self.player.controls['right'] = False
            
            # update delta time
            self.dt = (time.time() - self.last_time) * 60
            self.last_time = time.time()

            if self.state == "menu":
                self.menu()
            elif self.state == "game":
                # update game
                self.update()
            elif self.state == "game_over":
                self.game_over()
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
                self.display.blit(pygame.transform.scale2x(self.screen), (0, 0))
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
