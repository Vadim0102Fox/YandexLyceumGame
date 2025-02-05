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
    """
    Класс для создания интерактивных кнопок GUI.
    """
    def __init__(self, pos, image_default, image_active=None, action=None, *groups):
        super().__init__(*groups)
        self.image_default = image_default
        self.image_active = image_active
        self.image = self.image_default
        self.rect = self.image_default.get_rect()
        self.rect.topleft = pos
        self.func = action

    def update(self):
        """
        Обновляет состояние кнопки в зависимости от позиции мыши.
        Если мышь находится над кнопкой, меняет изображение и выполняет действие при нажатии.
        """
        x, y = pygame.mouse.get_pos()
        if self.rect.collidepoint(x, y):
            self.image = self.image_active
            if self.func is not None and pygame.mouse.get_pressed()[0]:
                return self.func()
        else:
            self.image = self.image_default


class Image(pygame.sprite.Sprite):
    """
    Класс для отображения статических изображений.
    """
    def __init__(self, pos, image_default, image_active=None, *groups):
        super().__init__(*groups)
        self.image_default = image_default
        self.image_active = image_active
        self.image = self.image_default
        self.rect = self.image_default.get_rect()
        self.rect.topleft = pos
        self.has_collision = False  # По умолчанию столкновения отключены

    def update(self):
        """
        Обновляет изображение, если есть активное изображение и курсор над ним.
        """
        x, y = pygame.mouse.get_pos()
        if self.image_active:
            if self.rect.collidepoint(x, y):
                self.image = self.image_active
            else:
                self.image = self.image_default


class Cursor(pygame.sprite.Sprite):
    """
    Класс для управления курсором, его движением и столкновениями.
    """
    def __init__(self, pos, image, level_objects=None, *groups):
        super().__init__(*groups)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.level_objects = level_objects
        self.load_objects(self.level_objects)
        self.prev_pos = pos

    def update(self, pos=None):
        """
        Обновляет позицию курсора, проверяет столкновения с объектами уровня.
        """
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
        if not objects:
            self.level_objects = pygame.sprite.Group()
            return
        self.level_objects = pygame.sprite.Group(tuple(filter(lambda obj: obj.has_collision, objects)))


class Wall(pygame.sprite.Sprite):
    """
    Класс для создания стен.
    """
    def __init__(self, pos, image=None, *groups):
        super().__init__(*groups)
        pos = correct_area_coords(pos)
        if image:
            self.image = image
        else:
            # print(pos)
            self.image = pygame.Surface((pos[2] - pos[0], pos[3] - pos[1]))
        self.rect = self.image.get_rect()
        self.rect.topleft = (pos[0], pos[1])
        self.has_collision = True  # По умолчанию столкновения включены


class RedWall(Wall):
    """
    Класс для создания красных стен (специальный тип стен).
    """
    def __init__(self, pos, *groups):
        super().__init__(pos, *groups)
        self.image.fill((255, 0, 0))
        self.has_collision = True  # По умолчанию столкновения включены


class AnimatedFinish(pygame.sprite.Sprite):
    """
    Класс для создания анимированного финиша уровня.
    """
    def __init__(self, pos, image=None, clip_height=10, speed=1, pause_duration=30, *groups):
        super().__init__(*groups)
        self.x1, self.y1, self.x2, self.y2 = correct_area_coords(pos)
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
        """
        Создает изображение в виде шахматной доски.
        """
        img = pygame.Surface(size)
        for row in range(size[1] // cell_size):
            for col in range(size[0] // cell_size):
                color = 'black' if (row + col) % 2 == 0 else 'white'
                pygame.draw.rect(img, color, (col * cell_size, row * cell_size, cell_size, cell_size))
        return img

    def update(self):
        """
        Обновляет анимацию финиша и проверяет столкновение с курсором.
        При столкновении загружает следующий уровень.
        """
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
    """
    Класс для загрузки и управления уровнем игры.
    """
    # Словарь для сопоставления имен объектов и классов
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
        self.levels_ended = False
        self.load()

    def load(self, file_name=None):
        """
        Загружает уровень из файла.
        """
        self.sprites = pygame.sprite.Group()
        if file_name is None:
            if self.cur_level >= len(self.file_names):
                self.levels_ended = True
                return False
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
        return True


class Timer(pygame.sprite.Sprite):
    """
    Класс для внутри-игрового таймера.
    """
    font = pygame.font.SysFont('Comic Sans MS', 30)

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((70, 30), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.topright = (WIDTH - 10, 5)
        self.value = 0
        self.event = pygame.USEREVENT + 2
        pygame.time.set_timer(self.event, 1000)
        self.update_next()

    def update_next(self):
        self.image.fill((0, 0, 0, 0))
        text_surface = self.font.render(str(self.value), True, (255, 155, 255))
        self.image.blit(text_surface, (70 - text_surface.get_width(), -6))


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


def correct_area_coords(*pos):
    if len(pos) == 1:
        x1, y1, x2, y2 = pos[0]
    else:
        x1, y1, x2, y2 = pos

    return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)


def start_window():
    """
    Отображает стартовое окно с кнопками "Играть" и "Правила".
    """
    im = load_image('start_window.png')
    all_sprites = pygame.sprite.Group()
    # Создание кнопок с использованием GUIButton
    play_button = GUIButton(
        (313, 407),
        load_image('play_button_default.png'),
        load_image('play_button_active.png'),
        lambda: True,
        all_sprites
    )
    rules_button = GUIButton(
        (10, 535),
        load_image('rules_button_default.png'),
        load_image('rules_button_active.png'),
        lambda: [rules_window()],
        all_sprites
    )

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        if play_button.update():
            return  # Нажата кнопка "Играть", выходим из стартового окна
        if rules_button.update():
            return  # Нажата кнопка "Правила", выходим из стартового окна

        # Отрисовка элементов стартового окна
        screen.fill((0, 0, 0))
        screen.blit(im, (0, 0))
        all_sprites.update()
        all_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(60)


def rules_window():
    """
    Отображает окно с правилами игры.
    """
    im = load_image('rules_window.png')
    all_sprites = pygame.sprite.Group()
    # Создание кнопки "Играть"
    play_button = GUIButton(
        (594, 520),
        load_image('play_button_default.png'),
        load_image('play_button_active.png'),
        lambda: True,
        all_sprites
    )

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        if play_button.update():
            return  # Нажата кнопка "Играть", выходим из окна правил

        # Отрисовка элементов окна правил
        screen.fill((0, 0, 0))
        screen.blit(im, (0, 0))
        all_sprites.update()
        all_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(60)


def pause_screen():
    """
    Отображает экран паузы
    """
    pause_surface = load_image('pause_window.png')
    prev_pos = pygame.mouse.get_pos()
    # screen.fill((100, 0, 100))
    screen.blit(pause_surface, (0, 0))
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return pygame.mouse.set_pos(prev_pos)

        clock.tick(60)


def end_screen():
    """
    Отображает экран окончания игры с результатами
    """
    best_available = False
    # Проверка наличия файла с лучшим рекордом
    if os.path.exists(os.path.join('data', 'best_record.txt')):
        with open(os.path.join('data', 'best_record.txt'), 'r') as f:
            best_value = int(f.readline().strip())
            best_minutes, best_seconds = best_value // 60, best_value % 60
            best_available = True

    font = pygame.font.SysFont('Comic Sans MS', 30)
    pygame.mouse.set_visible(True)  # Показываем курсор мыши

    value = timer.value
    minutes, seconds = value // 60, value % 60

    end_surface = load_image('end_window.png')
    screen.blit(end_surface, (0, 0))

    # Отображение текущего времени прохождения
    current_time_surface = font.render(f'Прохождение: {minutes}:{seconds}', True, (255, 255, 255))
    screen.blit(current_time_surface, (20, 200))

    # Отображение лучшего времени (если доступно)
    if best_available:
        if value < best_value:
            best_time_surface = font.render(f'Предыдущее лучшее время: {best_minutes}:{best_seconds}', True, (255, 255, 255))
            with open(os.path.join('data', 'best_record.txt'), 'w') as f:
                f.write(str(best_value))
        else:
            best_time_surface = font.render(f'Лучшее время: {best_minutes}:{best_seconds}', True, (255, 255, 255))
        screen.blit(best_time_surface, (20, 250))

    all_sprites = pygame.sprite.Group()
    # Создание кнопки "Назад"
    back_button = GUIButton(
        (600, 535),
        load_image('back_button_default.png'),
        load_image('back_button_active.png'),
        lambda: True,
        all_sprites
    )

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        if back_button.update():
            return  # Нажата кнопка "Назад", возвращаемся в главное меню

        all_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(60)


def main():
    global cursor
    global level
    global timer

    pygame.mouse.set_visible(False)  # Прячем системный курсор мыши
    timer = Timer()  # Создаем экземпляр таймера
    cursor = Cursor((WIDTH / 2, HEIGHT / 2), load_image('cursor.png'))  # Создаем экземпляр курсора
    cursor_group = pygame.sprite.Group((cursor, timer))  # Группа для курсора и таймера для удобства обновления и отрисовки
    files = [file for file in os.listdir('data') if file.startswith('level') and file.endswith('.csv')]
    sorted_files = sorted(files, key=lambda x: int(x[5:-4]))  # Обрезаем "level" и ".csv" и преобразуем в int
    level = Level(sorted_files)
    # level = Level(['level1.csv'])
    cursor.load_objects(level.sprites)  # Загружаем объекты уровня для обработки столкновений

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()  # Выход из игры при закрытии окна
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

        if level.levels_ended:
            return end_screen()  # Если все уровни пройдены, переходим на экран окончания игры

        # Отрисовка элементов игры
        screen.fill((255, 255, 255))  # Заливаем экран белым цветом
        level.sprites.update()  # Обновляем спрайты уровня
        level.sprites.draw(screen)  # Отрисовываем спрайты уровня
        cursor_group.update()  # Обновляем спрайты курсора
        cursor_group.draw(screen)  # Отрисовываем спрайты курсора
        pygame.display.flip()  # Обновляем экран
        clock.tick(60)  # Контролируем FPS


if __name__ == '__main__':
    while True:
        start_window()  # Отображаем стартовое окно
        main()  # Запускаем основную игру
