from util import read_json

TILE_SIZE = 8
# offsets set
OFFSETS = {(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (0, 0)}
PHYSICS_TILES = {'stone', 'cloud'}

class TileMap:
    def __init__(self, app):
        self.app = app
        self.tile_map = {}
        self.off_grid = []

    def load(self, path):
        # open file
        data = read_json(path)

        self.tile_map = {}
        self.off_grid = []

        print(f"Loading level data from `{path}`")

        # load ongrid tiles
        for tile in data['level']['tiles']:
            tile_loc = f"{tile['pos'][0]};{tile['pos'][1]}"
            self.tile_map[tile_loc] = {'type': tile['type'], 'variant': tile['variant'], 'timer': 0}

        # load off grid tiles
        self.off_grid.extend(data['level']['off_grid'])
        for tile in self.off_grid:
            tile['type'] = tile['type']

    def solid_check(self, pos):
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tile_map:
            if self.tile_map[tile_loc]['type'] in PHYSICS_TILES:
                return self.tile_map[tile_loc]

    def draw(self, surf, scroll):
        for tile in self.off_grid:
            surf.blit(self.app.assets[tile['type']][tile['variant']], (tile['pos'][0] - scroll[0], tile['pos'][1] - scroll[1]))

        for x in range(scroll[0] // self.tile_size, (scroll[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(scroll[1] // self.tile_size, (scroll[1] + surf.get_height()) // self.tile_size + 1):
                loc = str(x) + ';' + str(y)
                if loc in self.tile_map:
                    tile = self.tile_map[loc]
                    surf.blit(self.app.assets[tile['type']][tile['variant']], (tile['pos'][0] * self.tile_size - scroll[0], tile['pos'][1] * self.tile_size - scroll[1]))