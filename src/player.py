import pygame, math

class Anim:
    def __init__(self, speed, anim, anim_offset=[0, 0], loop=True):
        self.frame = 0
        self.speed = speed
        self.anim = list(anim)
        self.anim_offset = anim_offset
        self.loop = loop
        self.step = 0
        self.flip = False
    
    def reset(self):
        self.step = 0
        self.frame = 0
    
    def update(self, dt):
        self.frame += self.speed * dt
        self.step = math.floor(self.frame) % len(self.anim)
        # print(self.step)
        if not self.loop:
            self.step = min(math.floor(self.frame), len(self.anim) - 1)

    def render(self, surf, scroll, pos):
        frame = pygame.transform.flip(self.anim[self.step], self.flip, False)
        surf.blit(frame, (pos[0] - scroll[0] + self.anim_offset[0], pos[1] - scroll[1] + self.anim_offset[1]))

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
        self.acceleration = 0.6     # How fast we accelerate when input is pressed
        self.deceleration = 0.1    # How fast we decelerate when no input (stronger than friction)
        self.air_acceleration = 0.25  # Reduced acceleration when in air
        self.air_deceleration = 0.98  # Slower deceleration in air
        self.friction = 0.8          # Ground friction (applied always)
        self.air_resistance = 0.95   # Air resistance (applied always in air) 
        self.max_speed = 3        # Maximum horizontal speed
        self.gravity = 0.25          # Gravity strength
        self.max_fall_speed = 6      # Terminal velocity
        self.jump_power = -4     # Jump strength (negative = upward)
        self.decel_threshold = 0.1   # Speed below which we stop completely
        # self.app.assets['sfx/raining'].play()

        self.flip = False
        self.idle = Anim(0.2, self.app.assets['player/idle'])
        self.run = Anim(0.3, self.app.assets['player/run'])
        self.jump = Anim(0.5, self.app.assets['player/jump'])
        self.land = Anim(0.3, self.app.assets['player/land'], loop=False)
        self.grounded = 99
    
    def update_anim(self, dt):
        if self.falling > 3:
            self.grounded = 0
            self.jump.update(dt)
            self.land.reset()
            self.idle.reset()
            self.run.reset()
        elif self.grounded < 30:
            self.jump.reset()
            self.idle.reset()
            self.run.reset()
            self.land.update(dt)
        elif abs(self.movement.x) > 0.01:
            self.land.reset()
            self.idle.reset()
            self.jump.reset()
            self.run.update(dt)
        else:
            self.land.reset()
            self.run.reset()
            self.jump.reset()
            self.idle.update(dt)

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.dimensions.x, self.dimensions.y)

    def update(self, dt, tile_map):
        # Check if player is on ground (for different physics)
        on_ground = self.falling < 5
        self.grounded += dt
        
        # Horizontal movement with enhanced acceleration/deceleration
        target_speed = 0
        input_pressed = False
        
        if self.controls['left']:
            self.flip = True
            target_speed = -self.max_speed
            input_pressed = True
        elif self.controls['right']:
            self.flip = False
            target_speed = self.max_speed
            input_pressed = True
        
        # Apply acceleration or deceleration
        speed_diff = target_speed - self.movement.x
        
        if on_ground:
            if input_pressed and abs(speed_diff) > 0.1:
                # Accelerating toward target speed
                self.movement.x += speed_diff * self.acceleration * dt
            elif not input_pressed:
                # No input - apply strong deceleration
                self.movement.x *= pow(self.deceleration, dt)
                # Stop completely if speed is very low
                if abs(self.movement.x) < self.decel_threshold:
                    self.movement.x = 0
            
            # Always apply base friction
            self.movement.x *= pow(self.friction, dt)
        else:
            if input_pressed and abs(speed_diff) > 0.1:
                # Air acceleration (reduced control)
                self.movement.x += speed_diff * self.air_acceleration * dt
            elif not input_pressed:
                # No input in air - gentle deceleration
                self.movement.x *= pow(self.air_deceleration, dt)
            
            # Always apply air resistance
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
        for rect in tile_map.physics_rects_around(r.center):
            if r.colliderect(rect):
                if fm.y >= 0:
                    r.bottom = rect.top
                    self.falling = 0
                    # Mark the tile as walked on when player lands on it
                    tile_map.mark_tile_walked_on((rect.centerx, rect.centery))
                elif fm.y < 0:
                    r.top = rect.bottom
                self.movement.y = 0
                self.collisions['up'] = True
                self.pos.y = r.y

        self.update_anim(dt)

    def draw(self, surf, scroll):
        if self.falling > 3:
            self.jump.flip = self.flip
            self.jump.render(surf, scroll, self.pos)
        elif self.grounded < 30:
            self.jump.flip = self.flip
            self.jump.render(surf, scroll, self.pos)
        elif abs(self.movement.x) > 0.1:
            self.jump.flip = self.flip
            self.jump.render(surf, scroll, self.pos)
        else:
            self.jump.flip = self.flip
            self.jump.render(surf, scroll, self.pos)
        # pygame.draw.rect(surf, (255, 0, 0), (self.pos.x - scroll[0], self.pos.y - scroll[1], self.dimensions.x, self.dimensions.y))