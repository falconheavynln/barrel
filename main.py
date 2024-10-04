import pygame

from os import listdir
from os.path import isfile, join

from math import sqrt
from random import randint

pygame.init()

WIDTH = 900
HEIGHT = 500
SCROLL = (WIDTH // 4, HEIGHT // 4)

FPS = 60

CAPTION = "survive"
PATH = "assets"
ICON = "icon.png"

wd = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(CAPTION)
pygame.display.set_icon(pygame.image.load(join(PATH, ICON)))


def load_sprite_sheets(path, width, height, flip=False):
    images = [f for f in listdir(path) if isfile(join(path, f))]
    allsprites = {}
    for image in images:
        spritesheet = pygame.image.load(join(path, image)).convert_alpha()
        sprites = []
        for i in range(spritesheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(spritesheet, (0, 0), rect)
            sprites.append(surface)
        if flip:
            allsprites[image.replace(".png", "") + "_right"] = sprites
            allsprites[image.replace(".png", "") + "_left"] = [
                pygame.transform.flip(sprite, True, False) for sprite in sprites
            ]
        else:
            allsprites[image.replace(".png", "")] = sprites
    return allsprites


class Player(pygame.sprite.Sprite):
    def __init__(self, rect, character, speed, mspeed):
        super().__init__()
        self.rect = rect
        self.character = character
        self.speed, self.mspeed = speed, mspeed
        self.animdelay = 2
        self.sprites = load_sprite_sheets(
            join(PATH, "characters", self.character), self.rect.w, self.rect.h, True
        )
        self.direction = "right"
        self.image = self.sprites["joe" + "_" + self.direction]
        self.movement = [0, 0]
        self.animcount = 0

    def loop(self, offset):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction, self.animcount = "left", 0
            self.movement[0] = (
                -self.mspeed
                if self.movement[0] <= -self.mspeed + self.speed
                else self.movement[0] - self.speed
            )
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction, self.animcount = "right", 0
            self.movement[0] = (
                self.mspeed
                if self.movement[0] >= self.mspeed - self.speed
                else self.movement[0] + self.speed
            )
        elif abs(self.movement[0]) < 0.1:
            self.movement[0] = 0
        else:
            self.movement[0] *= 0.9
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.direction, self.animcount = "left", 0
            self.movement[1] = (
                -self.mspeed
                if self.movement[1] <= -self.mspeed + self.speed
                else self.movement[1] - self.speed
            )
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.direction, self.animcount = "right", 0
            self.movement[1] = (
                self.mspeed
                if self.movement[1] >= self.mspeed - self.speed
                else self.movement[1] + self.speed
            )
        elif abs(self.movement[1]) < 0.1:
            self.movement[1] = 0
        else:
            self.movement[1] *= 0.9

        self.rect.x += self.movement[0]
        self.rect.y += self.movement[1]

        self.animcount = (
            (self.animcount + 1) // self.animdelay % len(self.sprites["joe_right"])
        )
        self.image = self.sprites["joe" + "_" + self.direction][self.animcount]


class Enemy(pygame.sprite.Sprite):
    def __init__(self, rect, character, speed, mspeed):
        super().__init__()
        self.rect = rect
        self.character = character
        self.speed, self.mspeed = speed, mspeed
        self.aggro = False
        self.animdelay = 2
        self.sprites = load_sprite_sheets(
            join(PATH, "enemies", self.character),
            self.rect.w,
            self.rect.h,
            True,
        )
        self.direction = "right"
        self.image = self.sprites[character + "_" + self.direction]
        self.movement = [0, 0]
        self.animcount = 0

    def loop(self, player, offset):
        x_dist = (player.rect.x - offset[0]) - (self.rect.x - offset[0])
        y_dist = (player.rect.y - offset[1]) - (self.rect.y - offset[1])
        total_dist = sqrt(abs(int(x_dist) ^ 2) + abs(int(y_dist) ^ 2))
        print(total_dist)
        if total_dist < 2.5:
            self.movement = [0, 0]
        else:
            speed_reduction = abs(total_dist / self.mspeed)
            try:
                self.movement = [
                    x_dist / speed_reduction,
                    y_dist / speed_reduction,
                ]
            except ZeroDivisionError:
                self.movement = [x_dist, y_dist]

            for i in [0, 1]:
                if self.movement[i] > self.mspeed:
                    self.movement[i] = self.mspeed
                if self.movement[i] < -self.mspeed:
                    self.movement[i] = -self.mspeed

        self.rect.x += self.movement[0]
        self.rect.y += self.movement[1]

        self.animcount = (
            (self.animcount + 1)
            // self.animdelay
            % len(self.sprites[self.character + "_right"])
        )
        self.image = self.sprites[self.character + "_" + self.direction][self.animcount]


def scroll(player, offset):
    if (
        player.rect.right - offset[0] >= WIDTH - SCROLL[0] and player.movement[0] > 0
    ) or ((player.rect.left - offset[0] <= SCROLL[0]) and player.movement[0] < 0):
        offset[0] += player.movement[0]
    if (
        player.rect.bottom - offset[1] >= HEIGHT - SCROLL[1] and player.movement[1] > 0
    ) or ((player.rect.top - offset[1] <= SCROLL[1]) and player.movement[1] < 0):
        offset[1] += player.movement[1]
    return offset


def draw(objects, offset, grass_offset):
    tile_image = pygame.image.load(join(PATH, "grass.png"))
    _, _, tile_width, tile_height = tile_image.get_rect()
    _ = [
        [
            wd.blit(
                tile_image,
                (
                    i * tile_width + grass_offset[i][j][0] - offset[0],
                    j * tile_height + grass_offset[i][j][1] - offset[1],
                ),
            )
            for j in range(HEIGHT * 10 // tile_height)
        ]
        for i in range(WIDTH * 10 // tile_width)
    ]

    for object in objects:
        wd.blit(object.image, (object.rect.x - offset[0], object.rect.y - offset[1]))

    return grass_offset


def main():
    player = Player(pygame.rect.Rect(WIDTH / 2, HEIGHT / 2, 64, 64), "joe", 1.5, 8)
    enemy = Enemy(pygame.rect.Rect(WIDTH / 2, HEIGHT / 2, 64, 64), "zombo", 1, 4)
    tile_image = pygame.image.load(join(PATH, "grass.png"))
    _, _, tile_width, tile_height = tile_image.get_rect()
    grass_offset = [
        [
            [randint(-20, 20) * 1.5, randint(-20, 20) * 1.5]
            for _ in range(HEIGHT * 10 // tile_height)
        ]
        for _ in range(WIDTH * 10 // tile_width)
    ]
    offset = [0, 0]

    clock = pygame.time.Clock()
    run = True
    while run:
        pygame.display.update()
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        wd.fill((26, 36, 112))
        offset = scroll(player, offset)
        player.loop(offset)
        enemy.loop(player, offset)
        draw([player, enemy], offset, grass_offset)

    pygame.quit()
    quit()


if __name__ == "__main__":
    main()
