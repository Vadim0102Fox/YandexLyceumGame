import math
import os
import sys
import pygame
import collisions

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Лабиринт в курсоре')
clock = pygame.time.Clock()


class GUIButton(pygame.sprite.Sprite):
    def __init__(self, pos, image_default, image_active=None, action=None, *groups):
        super().__init__(*groups)
        self.image_default = image_default
        self.image_active = image_active
        self.image = self.image_default
        self.rect = self.image_default.get_rect()
        self.rect.topleft = pos
        self.func = action

    def update(self):
        x, y = pygame.mouse.get_pos()
        if self.rect.collidepoint(x, y):
            self.image = self.image_active
            if self.func is not None and pygame.mouse.get_pressed()[0]:
                return self.func()
        else:
            self.image = self.image_default


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def start_window():
    im = load_image('start_window.png')
    all_sprites = pygame.sprite.Group()
    play_button = GUIButton((313, 407),
        load_image('play_button_default.png'), load_image('play_button_active.png'), lambda: True, all_sprites)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        if play_button.update():
            return
        screen.fill((0, 0, 0))
        screen.blit(im, (0, 0))
        all_sprites.update()
        all_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(60)


class Cursor(pygame.sprite.Sprite):
    def __init__(self, pos, image, level_objects=None, *groups):
        super().__init__(*groups)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.level_objects = level_objects
        self.prev_pos = pos

    def update(self, pos=None):
        if pos:
            self.rect.topleft = pos
            return
        x, y = pygame.mouse.get_pos()  # Получаем текущую позицию мыши
        current_pos = (x, y)

        if self.level_objects:
            collision_info = collisions.draw_line_and_check_collision(self.prev_pos, current_pos, self.level_objects)
            if collision_info:
                # Столкновение произошло!
                self.rect.topleft = collision_info['position_before']  # Устанавливаем курсор в позицию перед столкновением
                pygame.mouse.set_pos(self.rect.topleft)
            else:
                # Нет столкновений, перемещаем курсор в текущую позицию мыши.
                self.rect.topleft = current_pos
        else:
            # Если нет объектов уровня для проверки, просто перемещаем курсор.
            self.rect.topleft = current_pos

        # Обновляем prev_pos для следующего кадра!  Это КЛЮЧЕВОЙ момент.
        self.prev_pos = self.rect.topleft

    def load_objects(self, objects):
        self.level_objects = objects


class Wall(pygame.sprite.Sprite):
    def __init__(self, pos, image=None, *groups):
        super().__init__(*groups)
        if image:
            self.image = image
        else:
            print(pos)
            self.image = pygame.Surface((abs(pos[0] - pos[2]), abs(pos[1] - pos[3])))
        self.rect = self.image.get_rect()
        self.rect.topleft = (pos[0], pos[1])
        self.has_collision = True


class Level:
    names_to_classes = {
        'wall': Wall,
        'cursor': Cursor,
    }

    def __init__(self, file_name, cursor=None):
        self.file_name = file_name
        self.cursor = cursor
        self.sprites = pygame.sprite.Group()
        self.load()

    def load(self, file_name=None):
        if file_name is None:
            file_name = self.file_name
        with open(os.path.join('data', file_name), 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line.startswith('#'):
                    continue
                obj, *data = line.split(';')
                if obj == 'cursor' and self.cursor is not None:
                    self.cursor.update((int(data[0]), int(data[1])))
                elif obj in self.names_to_classes:
                    self.sprites.add(self.names_to_classes[obj](tuple(map(int, data))))


def pause_screen():
    prev_pos = pygame.mouse.get_pos()
    screen.fill((100, 0, 100))
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return pygame.mouse.set_pos(prev_pos)

        clock.tick(60)


def main():
    pygame.mouse.set_visible(False)
    cursor = Cursor((WIDTH / 2, HEIGHT / 2), load_image('cursor.png'))
    cursor_group = pygame.sprite.Group(cursor)
    level = Level('level1.csv', cursor)
    cursor.load_objects(level.sprites)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pygame.mouse.set_visible(True)
                    pause_screen()
                    pygame.mouse.set_visible(False)

        screen.fill((255, 255, 255))
        level.sprites.draw(screen)
        cursor_group.update()
        cursor_group.draw(screen)
        pygame.display.flip()
        clock.tick(60)


if __name__ == '__main__':
    start_window()
    main()
