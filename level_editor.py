import pygame, sys, time, math, json

# window dimensions
SCR_WIDTH = 2100
SCR_HEIGHT = 1200
SCALE = 3 # screen scaling

# tile size
TILE_SIZE = 8
# world is split into chunks (size = relative tilesize, actual pixel size = tile_size * chunk_size)
CHUNK_SIZE = 9
# level width (relative chunk size, "")
LEVEL_WIDTH = 20
LEVEL_HEIGHT = 20

# json map path
MAP = "data/maps/0.json"

# tile sets that can be autotiled
AUTO_TILE_TYPES = {'grass', 'cloud', 'rock', 'portal', 'moss'}
AUTO_TILE_MAP = {'0011': 1, '1011': 2, '1001': 3, '0001': 4, '0111': 5, '1111': 6, '1101': 7, '0101': 8,
                '0110': 9, '1110': 10, '1100': 11, '0100': 12, '0010': 13, '1010': 14, '1000': 15, '0000': 16}

# the editor
class Editor:
    def __init__(self):
        # window dimensions
        self.dimensions = pygame.Vector2(SCR_WIDTH, SCR_HEIGHT)
        # render surfaces
        self.screen = pygame.Surface(self.dimensions // SCALE)
        self.display = pygame.display.set_mode(self.dimensions)
        # clock
        self.clock = pygame.time.Clock()
        # scroll
        self.scroll = pygame.Vector2(0, 0)

        # keyboard controls
        self.controls = {"right": False, "left": False, "up": False, "down": False, "l_shift": False}

        # time step
        self.dt = 1
        self.last_time = time.time() - 1/60

        # flags
        self.running = True

        # level data
        self.tile_map = {}
        self.off_grid = []
        self.load(MAP)

        # assets
        self.assets = {
            "grass": self.load_tileset(pygame.image.load("data/images/tiles/grass.png").convert()),
            "cloud": self.load_tileset(pygame.image.load("data/images/tiles/cloud.png").convert()),
            "rock": self.load_tileset(pygame.image.load("data/images/tiles/rock.png").convert()),
            "moss": self.load_tileset(pygame.image.load("data/images/tiles/moss.png").convert()),
            "portal": self.load_tileset(pygame.image.load("data/images/tiles/portal_spritesheet.png").convert()),
            "large_decor": self.load_sheet(pygame.image.load("data/images/tiles/large_decor.png").convert_alpha(), [50, 50])
        }

        # set colorkeys
        for key in self.assets:
            for surf in self.assets[key]:
                surf.set_colorkey((0, 0, 0))

        # left click & right click flags
        self.click = False
        self.right_click = False

        # tile highlight rectangle
        self.select_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.select_surf.fill((255, 100, 0))
        self.select_surf.set_alpha(100)

        # list of tile types
        self.tile_list = list(self.assets)
        self.tile_type = 0
        self.tile_variant = 0

        # flag if tile to place is on or off the grid
        self.grid = True

    # create new level
    def create_new(self, path):
        f = open(path, 'w')
        # write basic json level data
        json.dump({'level': {'tiles': [], 'off_grid': []}}, f, separators=(',', ':'))
        f.close()

    # load json level data from path
    def load(self, path):
        try:
            # open file
            f = open(path, 'r')
            # load
            data = json.load(f)
            f.close()

            self.tile_map = {}
            self.off_grid = []

            print(f"Loading level data from `{path}`")

            # load ongrid tiles
            for tile in data['level']['tiles']:
                tile_loc = f"{tile['pos'][0]};{tile['pos'][1]}"
                self.tile_map[tile_loc] = {'type': tile['type'], 'variant': tile['variant']}

            # load off grid tiles
            self.off_grid.extend(data['level']['off_grid'])
            for tile in self.off_grid:
                tile['type'] = tile['type']

        # if map doesn't exist, create new one
        except FileNotFoundError:
            self.create_new(path)
            self.load(path)

    # save level data
    def save(self, path):
        with open(path, 'w') as f:
            tiles = []
            off_grid = []
            for loc in self.tile_map:
                tiles.append({'pos': [int(c) for c in loc.split(';')], 'type': self.tile_map[loc]['type'], 'variant': self.tile_map[loc]['variant']})
            for tile in self.off_grid:
                off_grid.append({'pos': tile['pos'], 'type': tile['type'], 'variant': tile['variant']});
            json.dump({'level': {'tiles': tiles, 'off_grid': off_grid}}, f, separators=(',', ':'))
            print(f"Saved level data to `{path}`")

    def auto_tile(self):
        for loc in self.tile_map:
            tile = self.tile_map[loc]
            aloc = ''
            tile_pos = [int(i) * TILE_SIZE for i in loc.split(';')]
            for shift in [(-1, 0), (0, -1), (1, 0), (0, 1)]:
                check_loc = str(math.floor(tile_pos[0] / TILE_SIZE) + shift[0]) + ';' + str(math.floor(tile_pos[1] / TILE_SIZE) + shift[1])
                if check_loc in self.tile_map:
                    if self.tile_map[check_loc]['type'] in AUTO_TILE_TYPES:
                        aloc += '1'
                    else:
                        aloc += '0'
                else:
                    aloc += '0'
            if tile['type'] in AUTO_TILE_TYPES:
                tile['variant'] = AUTO_TILE_MAP[aloc] - 1

    def close(self):
        self.running = False
        pygame.quit()
        sys.exit()

    def draw_tile_grid(self, scroll, size, color):
        tile_size = [TILE_SIZE * size[0], TILE_SIZE * size[1]]
        length = math.ceil(self.screen.get_width() / tile_size[0]) + 2
        height = math.ceil(self.screen.get_height() / tile_size[1]) + 2
        for x in range(length):
            pygame.draw.line(self.screen, color, ((x - 1) * tile_size[0] - (scroll[0] % tile_size[0]), 0), ((x - 1) * tile_size[0] - (scroll[0] % tile_size[0]), self.screen.get_height()))
        for y in range(height):
            pygame.draw.line(self.screen, color, (0, (y - 1) * tile_size[1] - (scroll[1] % tile_size[1])), (self.screen.get_width(), (y - 1) * tile_size[1] - (scroll[1] % tile_size[1])))

    def draw_grid(self):
        self.draw_tile_grid(self.scroll, [1, 1], (50, 50, 50))
        self.draw_tile_grid(self.scroll, [CHUNK_SIZE, CHUNK_SIZE], (100, 100, 255))
        pygame.draw.line(self.screen, (255, 255, 255), (-self.scroll.x, -self.scroll.y), (LEVEL_WIDTH * CHUNK_SIZE * TILE_SIZE - self.scroll.x, -self.scroll.y), 1)
        pygame.draw.line(self.screen, (255, 255, 255), (-self.scroll.x, -self.scroll.y), (-self.scroll.x, LEVEL_HEIGHT * CHUNK_SIZE * TILE_SIZE - self.scroll.y), 1)
        pygame.draw.line(self.screen, (255, 255, 255), (LEVEL_WIDTH * CHUNK_SIZE * TILE_SIZE - self.scroll.x, -self.scroll.y), (LEVEL_WIDTH * CHUNK_SIZE * TILE_SIZE - self.scroll.x, LEVEL_HEIGHT * CHUNK_SIZE * TILE_SIZE - self.scroll.y), 1)
        pygame.draw.line(self.screen, (255, 255, 255), (-self.scroll.x, LEVEL_HEIGHT * CHUNK_SIZE * TILE_SIZE - self.scroll.y), (LEVEL_WIDTH * CHUNK_SIZE * TILE_SIZE - self.scroll.x, LEVEL_HEIGHT * CHUNK_SIZE * TILE_SIZE - self.scroll.y), 1)

    def draw_tiles(self):
        for x in range(math.floor(self.scroll.x / TILE_SIZE), math.floor((self.scroll.x + self.screen.get_width()) // TILE_SIZE + 1)):
            for y in range(math.floor(self.scroll.y / TILE_SIZE), math.floor((self.scroll.y + self.screen.get_height()) // TILE_SIZE + 1)):
                loc = str(x) + ';' + str(y)
                if loc in self.tile_map:
                    self.screen.blit(self.assets[self.tile_map[loc]["type"]][self.tile_map[loc]['variant']], (x * TILE_SIZE - self.scroll.x, y * TILE_SIZE - self.scroll.y))

    def load_tileset(self, sheet):
        tiles = []
        for y in range(4):
            for x in range(4):
                tile_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                tile_surf.blit(sheet, (-x * TILE_SIZE, -y * TILE_SIZE))
                tile_surf.set_colorkey((0, 0, 0))
                tiles.append(tile_surf)
        return tiles

    def load_sheet(self, sheet, tile_size):
        tiles = []
        for x in range(math.floor(sheet.get_width() / tile_size[0])):
            tile_surf = pygame.Surface(tile_size)
            tile_surf.blit(sheet, (-x * tile_size[0], 0))
            tile_surf.set_colorkey((0, 0, 0))
            tiles.append(tile_surf)
        return tiles

    def update(self):
        self.scroll.x += (int(self.controls['right']) - int(self.controls['left'])) * 5 * self.dt
        self.scroll.y += (int(self.controls['down']) - int(self.controls['up'])) * 5 * self.dt

        # add tiles
        mouse_pos = pygame.mouse.get_pos()
        mouse_pos = [math.floor((mouse_pos[0] / SCALE + self.scroll.x) / TILE_SIZE), math.floor((mouse_pos[1] / SCALE + self.scroll.y) / TILE_SIZE)]

        if self.click and self.grid:
            if 0 <= mouse_pos[0] < LEVEL_WIDTH * CHUNK_SIZE and 0 <= mouse_pos[1] < LEVEL_HEIGHT * CHUNK_SIZE:
                tile_loc = f"{mouse_pos[0]};{mouse_pos[1]}"
                if tile_loc in self.tile_map:
                    if self.tile_map[tile_loc]['type'] == self.tile_list[self.tile_type] and self.tile_map[tile_loc]['variant'] == self.tile_variant:
                        pass
                    else:
                        self.tile_map[tile_loc] = {'type': self.tile_list[self.tile_type], 'variant': self.tile_variant}
                else:
                    self.tile_map[tile_loc] = {'type': self.tile_list[self.tile_type], 'variant': self.tile_variant}
        if self.right_click and self.grid:
            if 0 <= mouse_pos[0] < LEVEL_WIDTH * CHUNK_SIZE and 0 <= mouse_pos[1] < LEVEL_HEIGHT * CHUNK_SIZE:
                tile_loc = f"{mouse_pos[0]};{mouse_pos[1]}"
                if tile_loc in self.tile_map:
                    del self.tile_map[tile_loc]

        # ---------- Do drawing ---------- #
        self.screen.fill((0, 0, 0))
        self.draw_grid()
        for tile in self.off_grid: # tile: [pos, type, variant] absolute pos
            self.screen.blit(self.assets[tile['type']][tile['variant']], (tile['pos'][0] - self.scroll.x, tile['pos'][1] - self.scroll.y))
        self.draw_tiles()

        mouse_pos = pygame.mouse.get_pos()
        if self.grid:
            mouse_pos = [math.floor((mouse_pos[0] / SCALE + self.scroll.x) / TILE_SIZE), math.floor((mouse_pos[1] / SCALE + self.scroll.y) / TILE_SIZE)]
            self.screen.blit(self.select_surf, (mouse_pos[0] * TILE_SIZE - self.scroll.x, mouse_pos[1] * TILE_SIZE - self.scroll.y))
            if not self.right_click:
                self.screen.blit(self.assets[self.tile_list[self.tile_type]][self.tile_variant], (mouse_pos[0] * TILE_SIZE - self.scroll.x, mouse_pos[1] * TILE_SIZE - self.scroll.y))
        else:
            mouse_pos = [math.floor(mouse_pos[0] / SCALE + self.scroll.x), math.floor(mouse_pos[1] / SCALE + self.scroll.y)]
            self.screen.blit(self.select_surf, (mouse_pos[0] - self.scroll.x, mouse_pos[1] - self.scroll.y))
            if not self.right_click:
                self.screen.blit(self.assets[self.tile_list[self.tile_type]][self.tile_variant], (mouse_pos[0] - self.scroll.x, mouse_pos[1] - self.scroll.y))

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.close()
                    elif event.key == pygame.K_t:
                        self.auto_tile()
                    elif event.key == pygame.K_o:
                        self.save(MAP)
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.controls["right"] = True
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.controls["left"] = True
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.controls["up"] = True
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.controls["down"] = True
                    elif event.key == pygame.K_LSHIFT:
                        self.controls['l_shift'] = True
                    elif event.key == pygame.K_g:
                        self.grid = not self.grid
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.controls["right"] = False
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.controls["left"] = False
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.controls["up"] = False
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.controls["down"] = False
                    elif event.key == pygame.K_LSHIFT:
                        self.controls['l_shift'] = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.click = True
                    elif event.button == 3:
                        self.right_click = True
                    elif self.controls['l_shift']:
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_type]])
                        elif event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_type]])
                    else:
                        if event.button == 4:
                            self.tile_type = (self.tile_type - 1) % len(self.tile_list)
                            self.tile_variant = 0
                        elif event.button == 5:
                            self.tile_type = (self.tile_type + 1) % len(self.tile_list)
                            self.tile_variant = 0
                    if not self.grid:
                        mouse_pos = pygame.mouse.get_pos()
                        mouse_pos = [math.floor(mouse_pos[0] / SCALE + self.scroll.x), math.floor(mouse_pos[1] / SCALE + self.scroll.y)]
                        if self.click:
                            if 0 <= mouse_pos[0] < LEVEL_WIDTH * CHUNK_SIZE * TILE_SIZE and 0 <= mouse_pos[1] < LEVEL_HEIGHT * CHUNK_SIZE * TILE_SIZE:
                                self.off_grid.append({'pos': mouse_pos, 'type': self.tile_list[self.tile_type], 'variant': self.tile_variant})
                        if self.right_click:
                            for i, tile in sorted(enumerate(self.off_grid), reverse=True):
                                tile_img = self.assets[tile['type']][tile['variant']];
                                tile_rect = pygame.Rect(tile['pos'][0], tile['pos'][1], tile_img.get_width(), tile_img.get_height())
                                if tile_rect.collidepoint(mouse_pos[0], mouse_pos[1]):
                                    self.off_grid.pop(i)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.click = False
                    if event.button == 3:
                        self.right_click = False

            self.update()

            pygame.transform.scale(self.screen, (SCR_WIDTH, SCR_HEIGHT), self.display)
            pygame.display.set_caption(f"FPS: {self.clock.get_fps() :.1f}")
            pygame.display.flip()
            self.clock.tick()

            # update deltatime
            self.dt = time.time() - self.last_time
            self.dt *= 60
            self.last_time = time.time()

if __name__ == "__main__":
    Editor().run()