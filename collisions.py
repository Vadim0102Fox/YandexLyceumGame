# Функция для определения стороны столкновения
import math
import pygame


def get_collision_side(rect1, rect2):
    """
    Определяет сторону столкновения двух прямоугольников.

    Возвращает строку: "top", "bottom", "left", "right" или None, если нет столкновения.
    """
    dx = (rect1.centerx - rect2.centerx) / rect2.width
    dy = (rect1.centery - rect2.centery) / rect2.height
    #print(dx, dy)

    if abs(dx) > abs(dy):
        if dx > 0:
            return "right"
        else:
            return "left"
    else:
        if dy > 0:
            return "bottom"
        else:
            return "top"

# Функция для вычисления координат до столкновения
def get_position_before_collision(start_pos, current_pos, collided_rect):
    """
    Вычисляет позицию точки на линии непосредственно перед столкновением с прямоугольником.
    Возвращает кортеж (x, y) координат перед столкновением.
    """

    dx = current_pos[0] - start_pos[0]
    dy = current_pos[1] - start_pos[1]
    # расстояние от start_pos до current_pos
    distance = math.sqrt(dx**2 + dy**2)

    # Перебираем точки от start_pos до current_pos и проверяем когда только произошло столкновение.
    # Находим первую точку, где нет столкновения.
    num_steps = int(distance) if distance != 0 else 1

    # Ищем точку, где еще нет столкновения.
    last_valid_x = start_pos[0]
    last_valid_y = start_pos[1]

    for i in range(num_steps + 1):
        x = int(start_pos[0] + dx * i / num_steps)
        y = int(start_pos[1] + dy * i / num_steps)

        temp_rect = pygame.Rect(x, y, 1, 1)  #Точечная коллизия

        if not temp_rect.colliderect(collided_rect):
            # Если нет столкновения, сохраняем текущие координаты
            last_valid_x = x
            last_valid_y = y
        else:
            # Как только произошло столкновение, возвращаем предыдущие координаты
            return (last_valid_x, last_valid_y)

    # Если столкновения не произошло вообще, то возвращаем начальную точку.
    return start_pos

# Функция для рисования линии и проверки столкновений
def draw_line_and_check_collision(start_pos, end_pos, sprites, width = 1):
    """
    Рисует линию между start_pos и end_pos и проверяет столкновения с спрайтами.
    Возвращает словарь с информацией о столкновении, если оно произошло, иначе None.
    Словарь содержит:
        - 'sprite': Спрайт, с которым произошло столкновение.
        - 'side': Сторона столкновения ("top", "bottom", "left", "right").
        - 'position_before': Координаты (x, y) точки на линии непосредственно перед столкновением.
    """

    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    distance = math.sqrt(dx**2 + dy**2)

    num_steps = int(distance) if distance != 0 else 1

    for i in range(num_steps + 1):
        x = int(start_pos[0] + dx * i / num_steps)
        y = int(start_pos[1] + dy * i / num_steps)
        temp_rect = pygame.Rect(x, y, width, width)

        for sprite in sprites:
            if temp_rect.colliderect(sprite.rect):
                side = get_collision_side(temp_rect, sprite.rect)
                position_before = get_position_before_collision(start_pos, (x, y), sprite.rect)

                return {
                    'sprite': sprite,
                    'side': side,
                    'position_before': position_before
                }

    return None
