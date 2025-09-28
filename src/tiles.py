import pygame
from .util import read_json

TILE_SIZE = 8
# offsets set
OFFSETS = {(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (0, 0)}
PHYSICS_TILES = {'stone', 'cloud', 'grass'}
# tiles that can be destroyed after being walked on
DESTRUCTIBLE_TILES = {'grass'}
# time in seconds before tile destroys after being walked on
DESTRUCTION_TIME = 0.00001

class TileMap:
    def __init__(self, app):
        self.app = app
        self.tile_map = {}
        self.off_grid = []
        self.tile_size = TILE_SIZE

    def load(self, path):
        # open file
        data = read_json(path)

        self.tile_map = {}
        self.off_grid = []

        print(f"Loading level data from `{path}`")

        # load ongrid tiles
        for tile in data['level']['tiles']:
            tile_loc = f"{tile['pos'][0]};{tile['pos'][1]}"
            self.tile_map[tile_loc] = {
                'type': tile['type'], 
                'variant': tile['variant'], 
                'timer': 0, 
                'pos': tile['pos'],
                'walked_on': False,
                'destruction_timer': 0.0
            }

        # load off grid tiles
        self.off_grid.extend(data['level']['off_grid'])
        for tile in self.off_grid:
            tile['type'] = tile['type']

    def tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tile_map:
                tiles.append(self.tile_map[check_loc])
        return tiles

    def solid_check(self, pos):
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tile_map:
            if self.tile_map[tile_loc]['type'] in PHYSICS_TILES:
                return self.tile_map[tile_loc]
    
    def get_adjacent_tiles(self, tile_loc):
        """Get all adjacent tiles (including diagonals) for a given tile location"""
        adjacent_tiles = []
        # Parse the tile location
        x, y = map(int, tile_loc.split(';'))
        
        # Check all surrounding blocks (including diagonals) using OFFSETS
        for dx, dy in OFFSETS:
            if (dx, dy) == (0, 0):  # Skip the center tile
                continue
            adj_loc = f"{x + dx};{y + dy}"
            if adj_loc in self.tile_map:
                adjacent_tiles.append(adj_loc)
        
        return adjacent_tiles
    
    def mark_tile_for_destruction(self, tile_loc, delay=0.0):
        """Mark a tile for destruction with optional delay"""
        if tile_loc in self.tile_map:
            tile = self.tile_map[tile_loc]
            if tile['type'] in DESTRUCTIBLE_TILES and not tile['walked_on']:
                tile['walked_on'] = True
                tile['destruction_timer'] = DESTRUCTION_TIME + delay
                print(f"Marked tile {tile_loc} for destruction in {DESTRUCTION_TIME + delay} seconds")
        else:
            print(f"Tile {tile_loc} not found in tile_map")
    
    def mark_tile_walked_on(self, pos):
        """Mark a tile as walked on to start its destruction timer and mark adjacent tiles"""
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        print(f"Marking tile at {tile_loc} for destruction")
        
        # Mark the main tile for destruction
        self.mark_tile_for_destruction(tile_loc)
        
        # Mark all adjacent tiles for destruction with a small delay
        adjacent_tiles = self.get_adjacent_tiles(tile_loc)
        print(f"Found {len(adjacent_tiles)} adjacent tiles to destroy")
        for adj_tile_loc in adjacent_tiles:
            # Add a small stagger delay for visual effect
            delay = 0.2  # 0.2 second delay for adjacent tiles
            self.mark_tile_for_destruction(adj_tile_loc, delay)
    
    def update(self, dt):
        """Update tile destruction timers"""
        tiles_to_remove = []
        tiles_to_cascade = []  # Tiles that will trigger adjacent destruction
        
        for tile_loc, tile in self.tile_map.items():
            if tile['walked_on'] and tile['type'] in DESTRUCTIBLE_TILES:
                tile['destruction_timer'] -= dt
                
                if tile['destruction_timer'] <= 0:
                    tiles_to_remove.append(tile_loc)
                    tiles_to_cascade.append(tile_loc)
                    # Play explosion sound when tile is destroyed
                    if 'sfx/explosion' in self.app.assets:
                        self.app.assets['sfx/explosion'].play()
        
        # Remove destroyed tiles
        for tile_loc in tiles_to_remove:
            if tile_loc in self.tile_map:  # Safety check
                del self.tile_map[tile_loc]
        
        # Cascade destruction to adjacent tiles (optional chain reaction)
        # Uncomment the lines below if you want chain reactions
        # for tile_loc in tiles_to_cascade:
        #     adjacent_tiles = self.get_adjacent_tiles(tile_loc)
        #     for adj_tile_loc in adjacent_tiles:
        #         self.mark_tile_for_destruction(adj_tile_loc, 0.3)  # Chain reaction delay
    
    def physics_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
        # print(rects)
        return rects

    def draw(self, surf, scroll):
        for tile in self.off_grid:
            surf.blit(self.app.assets[f"tiles/{tile['type']}"][tile['variant']], (tile['pos'][0] - scroll[0], tile['pos'][1] - scroll[1]))

        for x in range(scroll[0] // self.tile_size, (scroll[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(scroll[1] // self.tile_size, (scroll[1] + surf.get_height()) // self.tile_size + 1):
                loc = str(x) + ';' + str(y)
                if loc in self.tile_map:
                    tile = self.tile_map[loc]
                    tile_surf = self.app.assets[f"tiles/{tile['type']}"][tile['variant']].copy()
                    
                    # Add visual feedback for tiles that are about to be destroyed
                    if tile['walked_on'] and tile['type'] in DESTRUCTIBLE_TILES:
                        # Calculate how much time is left (0.0 to 1.0)
                        time_left = tile['destruction_timer'] / DESTRUCTION_TIME
                        
                        # Create a flashing/fading effect
                        if time_left < 0.5:  # Start flashing when less than half time left
                            flash_intensity = int((1 - time_left * 2) * 100)  # 0 to 100
                            # Make tile flash red
                            red_overlay = pygame.Surface((self.tile_size, self.tile_size))
                            red_overlay.fill((255, 100, 100))
                            red_overlay.set_alpha(flash_intensity)
                            tile_surf.blit(red_overlay, (0, 0))
                        
                        # Make tile more transparent as it approaches destruction
                        alpha = int(time_left * 255)
                        tile_surf.set_alpha(alpha)
                    
                    surf.blit(tile_surf, (tile['pos'][0] * self.tile_size - scroll[0], tile['pos'][1] * self.tile_size - scroll[1]))