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
    rules_button = GUIButton((10, 535),
        load_image('rules_button_default.png'), load_image('rules_button_active.png'), lambda: [rules_window()], all_sprites)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        if play_button.update():
            return
        if rules_button.update():
            return
        screen.fill((0, 0, 0))
        screen.blit(im, (0, 0))
        all_sprites.update()
        all_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(60)


def rules_window():
    im = load_image('rules_window.png')
    all_sprites = pygame.sprite.Group()
    play_button = GUIButton((594, 520),
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


class Image(pygame.sprite.Sprite):
    def __init__(self, pos, image_default, image_active=None, *groups):
        super().__init__(*groups)
        self.image_default = image_default
        self.image_active = image_active
        self.image = self.image_default
        self.rect = self.image_default.get_rect()
        self.rect.topleft = pos
        self.has_collision = False

    def update(self):
        x, y = pygame.mouse.get_pos()
        if self.image_active:
            if self.rect.collidepoint(x, y):
                self.image = self.image_active
            else:
                self.image = self.image_default


class Cursor(pygame.sprite.Sprite):
    def __init__(self, pos, image, level_objects=None, *groups):
        super().__init__(*groups)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.level_objects = level_objects
        self.load_objects(self.level_objects)
        self.prev_pos = pos

    def update(self, pos=None):
        if pos:
            self.prev_pos = pos
            self.rect.topleft = pos
            return

        x, y = pygame.mouse.get_pos()  # Получаем текущую позицию мыши
        current_pos = (x, y)

        if self.level_objects:
            collision_info = collisions.draw_line_and_check_collision(self.prev_pos, current_pos, self.level_objects)
            if collision_info:
                # Столкновение произошло!
                self.rect.topleft = collision_info['position_before']  # Устанавливаем курсор в позицию перед столкновением
                if type(collision_info['sprite']) is RedWall:
                    self.rect.topleft = level.mouse_pos
                pygame.mouse.set_pos(self.rect.topleft)
            else:
                # Нет столкновений, перемещаем курсор в текущую позицию мыши.
                self.rect.topleft = current_pos
        else:
            # Если нет объектов уровня для проверки, просто перемещаем курсор.
            self.rect.topleft = current_pos

        self.prev_pos = self.rect.topleft

    def load_objects(self, objects):
        if objects:
            self.level_objects = pygame.sprite.Group(tuple(filter(lambda obj: obj.has_collision, objects)))


class Wall(pygame.sprite.Sprite):
    def __init__(self, pos, image=None, *groups):
        super().__init__(*groups)
        if image:
            self.image = image
        else:
            # print(pos)
            self.image = pygame.Surface((abs(pos[0] - pos[2]), abs(pos[1] - pos[3])))
        self.rect = self.image.get_rect()
        self.rect.topleft = (pos[0], pos[1])
        self.has_collision = True


class RedWall(Wall):
    def __init__(self, pos, *groups):
        super().__init__(pos, *groups)
        self.image.fill((255, 0, 0))
        self.has_collision = True


class AnimatedFinish(pygame.sprite.Sprite):
    def __init__(self, pos, image=None, clip_height=10, speed=1, pause_duration=30, *groups):
        super().__init__(*groups)
        self.x1, self.y1, self.x2, self.y2 = pos
        self.width, self.height = abs(self.x1 - self.x2), abs(self.y1 - self.y2)
        self.clip_height, self.speed, self.pause_duration = clip_height, speed, pause_duration
        self.full_image = image if image else self.checkerboard((self.width, self.height * 2))
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(self.x1, self.y1))
        self.scroll_y = 0
        self.paused = False
        self.pause_timer = 0
        self.has_collision = False

    def checkerboard(self, size, cell_size=5):
        img = pygame.Surface(size)
        for row in range(size[1] // cell_size):
            for col in range(size[0] // cell_size):
                color = 'black' if (row + col) % 2 == 0 else 'white'
                pygame.draw.rect(img, color, (col * cell_size, row * cell_size, cell_size, cell_size))
        return img

    def update(self):
        if cursor:
            if self.rect.collidepoint(cursor.rect.topleft):
                print('!!!')
                level.load()

        if self.paused:
            self.pause_timer += 1
            if self.pause_timer >= self.pause_duration:
                self.paused = False
                self.pause_timer = 0
        else:
            self.scroll_y = (self.scroll_y + self.speed) % (self.full_image.get_height() - self.height)
            if self.scroll_y == 0:
                self.paused = True

        self.image.fill((0, 0, 0, 0))
        self.image.blit(self.full_image, (0, -self.scroll_y))
        if self.scroll_y > self.full_image.get_height() - self.height - self.clip_height:
            overlap = self.scroll_y - (self.full_image.get_height() - self.height - self.clip_height)
            self.image.blit(self.full_image, (0, self.height - overlap), (0, 0, self.width, overlap))


class Level:
    names_to_classes = {
        'wall': Wall,
        'finish': AnimatedFinish,
        'redwall': RedWall,
    }

    def __init__(self, file_names):
        self.file_names = file_names
        self.cur_level = 0
        self.sprites = pygame.sprite.Group()
        self.mouse_pos = (0, 0)
        self.load()

    def load(self, file_name=None):
        self.sprites = pygame.sprite.Group()
        if file_name is None:
            if self.cur_level >= len(self.file_names):
                return
            file_name = self.file_names[self.cur_level]
            self.cur_level += 1
        with open(os.path.join('data', file_name), 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                try:
                    obj, *data = line.split(';')
                    if obj == 'cursor':
                        cursor.update((int(data[0]), int(data[1])))
                        self.mouse_pos = (int(data[0]), int(data[1]))
                        pygame.mouse.set_pos((int(data[0]), int(data[1])))
                    elif obj == 'image':
                        im = load_image(data[0])
                        obj = Image(tuple(map(int, data[1:3])), im)
                        self.sprites.add(obj)
                    elif obj in self.names_to_classes:
                        obj = self.names_to_classes[obj](tuple(map(int, data)))
                        self.sprites.add(obj)
                    else:
                        print('unknown object in line:', line)
                except (ValueError, IndexError):
                    print('error when loading line:', line, '. skipping.')
        cursor.load_objects(self.sprites)


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


class Timer(pygame.sprite.Sprite):
    font = pygame.font.SysFont('comicsans', 30)

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((70, 30))
        self.image.fill((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.topright = (WIDTH - 10, 5)
        self.value = 0
        self.event = pygame.USEREVENT + 2
        pygame.time.set_timer(self.event, 1000)
        self.update_next()

    def update_next(self):
        self.image.fill((0, 0, 0))
        text_surface = self.font.render(str(self.value), True, (255, 155, 255))
        self.image.blit(text_surface, (70 - text_surface.get_width(), -6))


def main():
    global cursor
    global level

    pygame.mouse.set_visible(False)
    timer = Timer()
    cursor = Cursor((WIDTH / 2, HEIGHT / 2), load_image('cursor.png'))
    cursor_group = pygame.sprite.Group((cursor, timer))
    level = Level([file for file in os.listdir('data') if file.startswith('level')])
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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    print(event.pos)
            elif event.type == timer.event:
                timer.value += 1
                timer.update_next()

        screen.fill((255, 255, 255))
        level.sprites.update()
        level.sprites.draw(screen)
        cursor_group.update()
        cursor_group.draw(screen)
        pygame.display.flip()
        clock.tick(60)


if __name__ == '__main__':
    start_window()
    main()
