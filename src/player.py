import pygame

class Player:
    def __init__(self, app, dimensions, start_pos):
        self.app = app
        self.dimensions = pygame.Vector2(dimensions)
        self.start_pos = start_pos.copy()
        self.pos = pygame.Vector2(start_pos)

        self.falling = 30
        self.jumping = 30
        self.controls = {'up': False, 'down': False, 'left': False, 'right': False}

        self.movement = pygame.Vector2(0, 0)

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.dimensions.x, self.dimensions.y)

    def update(self, dt, tile_map):
        if self.controls['left']:
            self.movement.x -= 1.5 * dt
        if self.controls['right']:
            self.movement.x += 1.5 * dt

        self.movement.y += 0.1 * dt

        # frame movement
        fm = pygame.Vector2(self.movement.x * dt, self.movement.y * dt)
        
        self.pos.x += fm.x
        r = self.get_rect()
        for rect in tile_map.physics_rects_around(self.pos):
            if r.colliderect(rect):
                if fm.x > 0:
                    r.right = rect.left
                if fm.y < 0:
                    r.left = rect.right
                self.pos.x = r.x
                self.movement.x = 0

        # repeat for y-axis
        self.pos.y += fm.y
        r = self.get_rect()
        for rect in tile_map.physics_rects_around(self.pos):
            if r.colliderect(rect):
                if fm.y > 0:
                    r.bottom = rect.top
                    self.falling = 0
                if fm.y < 0:
                    r.top = rect.bottom
                self.pos.y = r.y
                self.movement.y = 0

    def draw(self, surf, scroll):
        pygame.draw.rect(surf, (255, 0, 0), self.get_rect())