import pygame, math, random

from .util import read_json
from .sparks import Spark

TILE_SIZE = 8
# offsets set
OFFSETS = {(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (0, 0)}
PHYSICS_TILES = {'rock', 'cloud', 'grass', 'moss'}
HOLLOW_TILES = {'portal'}
# tiles that can be destroyed after being walked on
DESTRUCTIBLE_TILES = {'cloud'}
# time in seconds before tile destroys after being walked on
DESTRUCTION_TIME = 0.4

AUTO_TILE_TYPES = {'grass', 'cloud', 'rock', 'moss'}
AUTO_TILE_MAP = {'0011': 1, '1011': 2, '1001': 3, '0001': 4, '0111': 5, '1111': 6, '1101': 7, '0101': 8,
                '0110': 9, '1110': 10, '1100': 11, '0100': 12, '0010': 13, '1010': 14, '1000': 15, '0000': 16}

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
        """Get all adjacent tiles for a given tile location"""
        adjacent_tiles = []
        # Parse the tile location
        x, y = map(int, tile_loc.split(';'))
        
        # Check all surrounding blocks using OFFSETS
        for dx, dy in OFFSETS:
            adj_loc = f"{x + dx};{y + dy}"
            if adj_loc in self.tile_map:
                adjacent_tiles.append(adj_loc)
        
        return adjacent_tiles
    
    def get_3x3_destruction_area(self, tile_loc):
        """Get a 3x3 area of tiles centered 1 block higher than the given tile location"""
        destruction_tiles = []
        # Parse the tile location
        x, y = map(int, tile_loc.split(';'))
        
        # Create 3x3 grid centered 1 block higher (y-1)
        center_x, center_y = x, y - 1
        
        # Generate 3x3 pattern around the center point
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                target_loc = f"{center_x + dx};{center_y + dy}"
                if target_loc in self.tile_map:
                    destruction_tiles.append(target_loc)
        
        return destruction_tiles
    
    def mark_tile_for_destruction(self, tile_loc, delay=0.0):
        """Mark a tile for destruction with optional delay"""
        if tile_loc in self.tile_map:
            tile = self.tile_map[tile_loc]
            if tile['type'] in DESTRUCTIBLE_TILES and not tile['walked_on']:
                tile['walked_on'] = True
                tile['destruction_timer'] = DESTRUCTION_TIME + delay
    
    def mark_tile_walked_on(self, pos):
        """Mark tiles in a 3x3 pattern centered 1 block higher than the landing position"""
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        
        # Get the 3x3 destruction area centered 1 block higher
        destruction_tiles = self.get_3x3_destruction_area(tile_loc)
        
        # Mark all tiles in the 3x3 area for destruction
        for i, target_tile_loc in enumerate(destruction_tiles):
            # Add a small stagger delay for visual effect (0.0 to 0.4 seconds)
            delay = i * 0.05  # Each tile destroys 0.05 seconds after the previous
            self.mark_tile_for_destruction(target_tile_loc, delay)
    
    def get_3x3_destruction_area(self, tile_loc):
        """Get a 3x3 area of tiles centered 1 block higher than the given tile location"""
        destruction_tiles = []
        # Parse the tile location
        x, y = map(int, tile_loc.split(';'))
        
        # Create 3x3 grid centered 1 block higher (y-1)
        center_x, center_y = x, y - 1
        
        # Generate 3x3 pattern around the center point
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                target_loc = f"{center_x + dx};{center_y + dy}"
                if target_loc in self.tile_map:
                    destruction_tiles.append(target_loc)
        
        return destruction_tiles
    
    def mark_tile_for_destruction(self, tile_loc, delay=0.0):
        """Mark a tile for destruction with optional delay"""
        if tile_loc in self.tile_map:
            tile = self.tile_map[tile_loc]
            if tile['type'] in DESTRUCTIBLE_TILES and not tile['walked_on']:
                tile['walked_on'] = True
                tile['destruction_timer'] = DESTRUCTION_TIME + delay
                # print(f"Marked tile {tile_loc} for destruction in {DESTRUCTION_TIME + delay} seconds")
        else:
            print(f"Tile {tile_loc} not found in tile_map")
    
    def mark_tile_walked_on(self, pos):
        """Mark tiles in a 3x3 pattern centered 1 block higher than the landing position"""
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        # print(f"Player landed on tile {tile_loc}, destroying 3x3 area centered 1 block higher")
        
        # Get the 3x3 destruction area centered 1 block higher
        destruction_tiles = self.get_3x3_destruction_area(tile_loc)
        # print(f"Found {len(destruction_tiles)} tiles in 3x3 destruction area")
        
        # Mark all tiles in the 3x3 area for destruction
        for i, target_tile_loc in enumerate(destruction_tiles):
            # Add a small stagger delay for visual effect (0.0 to 0.4 seconds)
            delay = i * 0.05  # Each tile destroys 0.05 seconds after the previous
            self.mark_tile_for_destruction(target_tile_loc, delay)
    
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
                        pass
                        self.app.assets['sfx/explosion'].play()
        
        # Remove destroyed tiles
        for tile_loc in tiles_to_remove:
            if tile_loc in self.tile_map:  # Safety check
                del self.tile_map[tile_loc]
                self.auto_tile()
                self.app.screen_shake = max(self.app.screen_shake, 6)
                tile_pos = [int(coord) * 8 for coord in tile_loc.split(';')]
                for _ in range(random.randint(10, 20)):
                    speed = random.random() + 2
                    angle = random.random() * math.pi * 2
                    self.app.kickup.append([[tile_pos[0] + random.random() * 8, tile_pos[1] + random.random() * 8], [math.cos(angle) * speed, math.sin(angle) * speed], random.random() + 9, random.choice(self.app.kickup_palette)])
                for _ in range(random.randint(10, 20)):
                    self.app.sparks.append(Spark([tile_pos[0] + random.random() * 8, tile_pos[1] + random.random() * 8], random.random() * 2 * math.pi, random.random() * 1.5 + 0.5, (255, 255, 255)))

        # Cascade destruction to adjacent tiles (optional chain reaction)
        # Uncomment the lines below if you want chain reactions
        # for tile_loc in tiles_to_cascade:
        #     adjacent_tiles = self.get_adjacent_tiles(tile_loc)
        #     for adj_tile_loc in adjacent_tiles:
        #         self.mark_tile_for_destruction(adj_tile_loc, 0.0)  # Chain reaction delay
    
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