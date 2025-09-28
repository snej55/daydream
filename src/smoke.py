import pygame, random

SMOKE_DELAY = 100
FADE = 4

class Smoke:
    def __init__(self, x, y, dx, dy, color):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.size = 100
        self.timer = 0
        self.img = pygame.Surface((self.size, self.size))
        pygame.draw.rect(self.img, color, (1, 1, self.size - 2, self.size - 2))
        self.img.set_colorkey((0, 0, 0))
        self.img.convert_alpha()
        self.target_angle = random.random() * 360 + 720
        self.angle = 0
        self.smoke = []
    
    @property
    def pos(self):
        return self.x, self.y
    
    def update(self, dt):
        self.x += self.dx * dt
        self.y += self.dy * dt
        self.dx += (self.dx * 0.989 - self.dx) * dt
        self.dy += (self.dy * 0.989 - self.dy) * dt
        self.timer += 1 * dt
        self.angle += (self.target_angle - self.angle) / 15 * dt
    
    def draw(self, surf, scroll=[0, 0]):
        self.img.set_alpha(int(255 - 255 * self.timer / SMOKE_DELAY * FADE))
        img_copy = pygame.transform.scale(pygame.transform.rotate(self.img, (self.angle)),
                                          (1 + self.size * self.timer / SMOKE_DELAY, 1 + self.size * self.timer / SMOKE_DELAY)).convert_alpha()
        surf.blit(img_copy, (self.x - scroll[0], self.y - scroll[1]))
