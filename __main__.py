import pygame

from os import listdir
from os.path import isfile, join

from math import sqrt, sin, pi
from random import randint


pygame.init()

WIDTH = 1000
HEIGHT = 650
SCROLL = (WIDTH // 3, HEIGHT // 3)

FPS = 60

CAPTION = "survive"
PATH = "assets"
ICON = "icon.png"

wd = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(CAPTION)
pygame.display.set_icon(pygame.image.load(join(PATH, ICON)))


def load_sprite_sheets(path, width, height, flip=False) -> dict:
    images = [f for f in listdir(path) if isfile(join(path, f))]
    allsprites = {}
    for image in images:
        spritesheet = pygame.image.load(join(path, image)).convert_alpha()
        sprites = []
        for i in range(spritesheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(spritesheet, (0, 0), rect)
            print(surface)
            sprites.append(surface)
        if flip:
            allsprites[image.replace(".png", "") + "_right"] = sprites
            allsprites[image.replace(".png", "") + "_left"] = [
                pygame.transform.flip(sprite, True, False) for sprite in sprites
            ]
        else:
            allsprites[image.replace(".png", "")] = sprites
    return allsprites


class Bullet(pygame.sprite.Sprite):
    def __init__(self, player, objects, offset, look_offset, rect, path) -> None:
        super().__init__()
        self.angle = player.angle
        self.speed = player.bullet_speed
        self.path = path
        self.rect = rect
        self.dead = False
        self.movement = []
        mouse_pos = pygame.mouse.get_pos()
        x_dist = (
            mouse_pos[0]
            - player.rect.centerx
            + offset[0]
            + look_offset[0]
            + player.rotation_offset
            - 29
        )
        y_dist = (
            mouse_pos[1]
            - player.rect.centery
            + offset[1]
            + look_offset[1]
            + player.rotation_offset
            - 29
        )
        total_dist = sqrt(abs(x_dist * x_dist) + abs(y_dist * y_dist))
        if total_dist == 0:
            self.dead = True
        else:
            self.movement = [
                (self.speed * x_dist) / total_dist,
                (self.speed * y_dist) / total_dist,
            ]
        self.loop(player, objects)
        self.rect.x -= self.movement[0]
        self.rect.y -= self.movement[1]

    def update_mask(self):
        self.mask = pygame.mask.from_surface(self.rotated_image)

    def loop(self, player, objects) -> None:
        self.rect.x += self.movement[0]
        self.rect.y += self.movement[1]

        self.image = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        self.bullet_image = pygame.image.load(
            join(PATH, "bullets", self.path + ".png")
        ).convert_alpha()
        self.image.blit(self.bullet_image, (0, 0))

        self.rotated_image = pygame.transform.rotate(self.image, self.angle)

        if (
            self.rect.x < player.rect.x - WIDTH
            or self.rect.y < player.rect.y - HEIGHT
            or self.rect.x > player.rect.x + WIDTH
            or self.rect.y > player.rect.y + HEIGHT
        ):
            self.dead = True
        for object in objects:
            if pygame.sprite.collide_mask(self, object):
                self.dead = True

        self.update_mask()


class Player(pygame.sprite.Sprite):
    def __init__(self, rect, character, gun, speed, mspeed) -> None:
        super().__init__()
        self.rect = rect
        self.character, self.gun = character, gun
        self.speed, self.mspeed = speed, mspeed
        self.animdelay = 2
        self.perception = 0.5  # higher is better
        self.angle = 0
        self.bullets = []
        self.loaded = 0
        self.reload = 10  # higher is worse
        self.bullet_speed = 15  # higher is better
        self.movement = [0, 0]
        self.animcount = 0
        self.mask = None

    def update_mask(self):
        self.mask = pygame.mask.from_surface(self.rotated_image)

    def loop(self, objects, offset, look_offset) -> None:
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

        if keys[pygame.K_p]:
            self.character = "green"
        elif keys[pygame.K_o]:
            self.character = "joe"

        if pygame.mouse.get_pressed(num_buttons=3)[0] and self.loaded >= 0:
            self.bullets.append(
                Bullet(
                    self,
                    objects,
                    offset,
                    look_offset,
                    pygame.rect.Rect(
                        self.rect.centerx - 32, self.rect.centery - 32, 64, 64
                    ),
                    "ammo",
                )
            )
            self.loaded = -self.reload
        elif self.loaded < 0:
            self.loaded += 1

        for bullet in self.bullets:
            if bullet.dead:
                self.bullets.remove(bullet)
            bullet.loop(self, objects)

        self.rect.x += self.movement[0]
        self.rect.y += self.movement[1]

        mouse_pos = pygame.mouse.get_pos()
        self.vector = pygame.Vector2(
            mouse_pos[0] - (self.rect.centerx - offset[0] - look_offset[0]),
            mouse_pos[1] - (self.rect.centery - offset[1] - look_offset[1]),
        )
        self.polar = self.vector.as_polar()
        self.angle = (-self.polar[1] + 360) % 360

        self.rads = self.angle / 360 * 2 * pi

        self.rotation_offset = self.rect.w * abs(sin(2 * self.rads)) * sqrt(2) / 7
        self.image = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        self.body_image = pygame.image.load(
            join(PATH, "characters", self.character + ".png")
        ).convert_alpha()
        self.gun_image = pygame.image.load(
            join(PATH, "guns", self.gun + ".png")
        ).convert_alpha()
        self.image.blit(self.body_image, (0, 0))
        self.image.blit(self.gun_image, (0, 0))

        self.rotated_image = pygame.transform.rotate(self.image, self.angle)

        self.update_mask()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, rect, character, speed, mspeed) -> None:
        super().__init__()
        self.rect = rect
        self.character = character
        self.speed, self.mspeed = speed, mspeed
        self.aggro = False
        self.dead = False
        self.animdelay = 2
        self.image = pygame.image.load(
            join(PATH, "enemies", character + ".png")
        ).convert_alpha()
        self.angle = 100
        self.movement = [0, 0]

    def update_mask(self):
        self.mask = pygame.mask.from_surface(self.rotated_image)

    def loop(self, player) -> None:
        x_dist = player.rect.centerx - self.rect.centerx + 32
        y_dist = player.rect.centery - self.rect.centery + 32
        total_dist = sqrt(abs(int(x_dist) ^ 2) + abs(int(y_dist) ^ 2))
        if total_dist < 2.5:
            self.movement = [0, 0]
        else:
            speed_reduction = abs(total_dist / self.mspeed)
            try:
                self.movement = [
                    x_dist / speed_reduction + randint(-20, 20),
                    y_dist / speed_reduction + randint(-20, 20),
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

        self.rotated_image = pygame.transform.rotate(self.image, self.angle)

        for bullet in player.bullets:
            if pygame.sprite.collide_mask(self, bullet):
                self.dead = True

        self.update_mask()


def scroll(player, offset) -> tuple[list]:
    look_offset = [0, 0]
    look_offset[0] = (pygame.mouse.get_pos()[0] - WIDTH // 2) * player.perception
    look_offset[1] = (pygame.mouse.get_pos()[1] - HEIGHT // 2) * player.perception
    if (
        player.rect.right - offset[0] >= WIDTH - SCROLL[0] and player.movement[0] > 0
    ) or ((player.rect.left - offset[0] <= SCROLL[0]) and player.movement[0] < 0):
        offset[0] += player.movement[0]
    if (
        player.rect.bottom - offset[1] >= HEIGHT - SCROLL[1] and player.movement[1] > 0
    ) or ((player.rect.top - offset[1] <= SCROLL[1]) and player.movement[1] < 0):
        offset[1] += player.movement[1]
    return offset, look_offset


def draw(objects, offset, look_offset) -> None:
    # print(objects[0].rect, offset)
    tile_image = pygame.image.load(join(PATH, "tile.png"))
    _, _, tile_width, tile_height = tile_image.get_rect()
    _ = [
        [
            wd.blit(
                tile_image,
                (
                    i * tile_width - ((offset[0] + look_offset[0]) % tile_width),
                    j * tile_height - ((offset[1] + look_offset[1]) % tile_height),
                ),
            )
            for j in range(HEIGHT // tile_height + 10)
        ]
        for i in range(WIDTH // tile_width + 10)
    ]

    # wd.blit(
    #     pygame.Surface((64, 64)),
    #     (
    #         objects[0].rect.centerx - offset[0] - look_offset[0],
    #         objects[0].rect.centery - offset[1] - look_offset[1],
    #     ),
    # )

    for object in objects:
        if type(object) is Player:
            wd.blit(
                object.rotated_image,
                (
                    object.rect.x - offset[0] - look_offset[0] - object.rotation_offset,
                    object.rect.y - offset[1] - look_offset[1] - object.rotation_offset,
                ),
            )
        else:
            wd.blit(
                object.rotated_image,
                (
                    object.rect.x - offset[0] - look_offset[0],
                    object.rect.y - offset[1] - look_offset[1],
                ),
            )


def main() -> None:
    player = Player(
        pygame.rect.Rect(WIDTH / 2 - 32, HEIGHT / 2 - 32, 128, 128),
        "default",
        "arrow",
        1.5,
        8,
    )
    enemies = [
        Enemy(
            pygame.rect.Rect(
                WIDTH / 2 + randint(-1000, 1000),
                HEIGHT / 2 + randint(-1000, 1000),
                128,
                128,
            ),
            "zombo",
            0.1,
            1,
        )
        for _ in range(20)
    ]
    offset, look_offset = [0, 0], [0, 0]

    clock = pygame.time.Clock()
    run = True
    while run:
        pygame.display.update()
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        offset, look_offset = scroll(player, offset)
        player.loop(enemies, offset, look_offset)
        for enemy in enemies:
            if enemy.dead:
                enemies.remove(enemy)
            else:
                enemy.loop(player)
        draw(player.bullets + enemies + [player], offset, look_offset)

    pygame.quit()
    quit()


if __name__ == "__main__":
    main()
