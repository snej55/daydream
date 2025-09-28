import pygame, os, json

BASE_IMG_PATH = 'data/images/'
BASE_AUDIO_PATH = 'data/sound/'

def load_image(path) -> pygame.Surface:
    surf = pygame.image.load(BASE_IMG_PATH + path).convert()
    surf.set_colorkey((0, 0, 0))
    return surf

def load_images(path):
    imgs = []
    for img_path in os.listdir(BASE_IMG_PATH + path):
        imgs.append(load_image(path + '/' + img_path))
    return imgs

def load_sound(path) -> pygame.mixer.Sound:
    path = 'data/sound/sfx/' + path
    return pygame.mixer.Sound(BASE_AUDIO_PATH + path)

def load_tile_imgs(path, tile_size):
    img = load_image(path)
    img_surf = pygame.Surface((tile_size, tile_size))
    tiles = []
    dimensions = [int(img.get_width() / tile_size), int(img.get_height() / tile_size)]
    for y in range(dimensions[1]):
        for x in range(dimensions[0]):
            img_surf.fill((0, 0, 0))
            img_surf.blit(img, (-x * tile_size, -y * tile_size))
            img_surf.convert()
            img_surf.set_colorkey((0, 0, 0))
            tiles.append(img_surf.copy())
    return tiles

def snip(spritesheet, pos, dimensions):
    clip_rect = pygame.Rect(pos, dimensions)
    image = spritesheet.subsurface(clip_rect)
    return image

def read_json(path):
    f = open(path, 'r')
    data = json.load(f)
    f.close()
    return data

def write_json(path, data):
    f = open(path, 'w')
    json.dump(data, f)
    f.close()

def load_palette(img: pygame.Surface):
    img_array = pygame.pixelarray.PixelArray(img)
    palette = []
    for row in img_array:
        for color in row:
            c = img.unmap_rgb(color)
            if c != (0, 0, 0, 0): palette.append(tuple(c))
    return palette