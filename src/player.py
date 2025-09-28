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
        self.collisions = {'up': False, 'down': False}

        self.movement = pygame.Vector2(0, 0)
        
        # More realistic physics constants
        self.acceleration = 0.9     # How fast we accelerate when input is pressed
        self.air_acceleration = 0.15  # Reduced acceleration when in air
        self.friction = 0.8          # Ground friction (0.8 = loses 20% speed per frame)
        self.air_resistance = 0.95   # Air resistance (0.95 = loses 5% speed per frame) 
        self.max_speed = 3        # Maximum horizontal speed
        self.gravity = 0.25          # Gravity strength
        self.max_fall_speed = 6      # Terminal velocity
        self.jump_power = -4.5      # Jump strength (negative = upward)

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.dimensions.x, self.dimensions.y)

    def update(self, dt, tile_map):
        # Check if player is on ground (for different physics)
        on_ground = self.falling < 5
        
        # Horizontal movement with realistic acceleration/deceleration
        target_speed = 0
        if self.controls['left']:
            target_speed = -self.max_speed
        elif self.controls['right']:
            target_speed = self.max_speed
        
        # Apply acceleration or deceleration
        speed_diff = target_speed - self.movement.x
        
        if on_ground:
            # Ground movement - faster acceleration and stronger friction
            if abs(speed_diff) > 0.1:  # Accelerating toward target
                self.movement.x += speed_diff * self.acceleration * dt
            # Apply ground friction
            self.movement.x *= pow(self.friction, dt)
        else:
            # Air movement - slower acceleration, less control
            if abs(speed_diff) > 0.1:
                self.movement.x += speed_diff * self.air_acceleration * dt
            # Apply air resistance
            self.movement.x *= pow(self.air_resistance, dt)
        
        # Clamp horizontal speed to max
        if abs(self.movement.x) > self.max_speed:
            self.movement.x = self.max_speed if self.movement.x > 0 else -self.max_speed
        
        # Vertical movement with realistic gravity
        self.collisions = {'up': False, 'down': False}
        
        # Apply gravity
        self.movement.y += self.gravity * dt
        
        # Clamp fall speed to terminal velocity
        if self.movement.y > self.max_fall_speed:
            self.movement.y = self.max_fall_speed

        self.falling += dt

        # Jumping with improved feel
        if self.controls['up'] and on_ground:
            self.movement.y = self.jump_power
            self.falling = 30

        # frame movement
        fm = pygame.Vector2(self.movement.x * dt, self.movement.y * dt)
        
        self.pos.x += fm.x
        r = self.get_rect()
        for rect in tile_map.physics_rects_around(r.center):
            if r.colliderect(rect):
                if fm.x > 0:
                    r.right = rect.left
                if fm.x < 0:
                    r.left = rect.right
                self.pos.x = r.x
                self.movement.x = 0

        self.pos.y += fm.y
        r = self.get_rect()
        ground_collision = False
        for rect in tile_map.physics_rects_around(r.center):
            if r.colliderect(rect):
                if fm.y >= 0:
                    r.bottom = rect.top
                    self.falling = 0
                    ground_collision = True
                    # Mark the tile as walked on when player lands on it
                    tile_map.mark_tile_walked_on((rect.centerx, rect.centery))
                    print(f"Player landed on tile at {rect.centerx}, {rect.centery}")
                elif fm.y < 0:
                    r.top = rect.bottom
                self.movement.y = 0
                self.collisions['up'] = True
                self.pos.y = r.y

    def draw(self, surf, scroll):
        pygame.draw.rect(surf, (255, 0, 0), (self.pos.x - scroll[0], self.pos.y - scroll[1], self.dimensions.x, self.dimensions.y))