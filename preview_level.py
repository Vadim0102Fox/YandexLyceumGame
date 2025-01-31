import os
import pygame
import main
import sys
import time
import re
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import queue
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Константы
LEVEL_FILE_REGEX = r"level\d+\.csv$"
TEMP_FILE_REGEX = r"level\d+\.csv~$"
DIRECTORY_TO_MONITOR = "data"

class MyHandler(FileSystemEventHandler):
    def __init__(self, changed_files_queue):
        self.changed_files_queue = changed_files_queue

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = Path(os.path.abspath(event.src_path))
        file_str = str(file_path)

        if re.search(LEVEL_FILE_REGEX, file_str) or re.search(TEMP_FILE_REGEX, file_str):
            if file_str.endswith("~"):
                base_file = Path(file_str[:-1])
                logging.info(f"Изменен временный файл, обрабатываем базовый: {base_file}")
                self.changed_files_queue.put(str(base_file))

            else:
                self.changed_files_queue.put(file_str)
            logging.info(f"Файл {file_path} был изменен!")


def monitor_files_watchdog(directory_path, changed_files_queue):
    event_handler = MyHandler(changed_files_queue)
    observer = Observer()
    observer.schedule(event_handler, path=directory_path, recursive=False)
    observer.start()
    logging.info(f"Наблюдение за изменениями в директории: {directory_path}")

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Наблюдение за файлами остановлено.")
    finally:
        observer.join()


def update_level(level, level_name, cursor):
    level.load(level_name)
    cursor.load_objects(level.sprites)
    logging.info(f"Уровень {level_name} обновлен!")


level_name = 'level1.csv'
cursor = main.Cursor((main.WIDTH / 2, main.HEIGHT / 2), main.load_image('cursor.png'))
cursor_group = pygame.sprite.Group(cursor)
main.cursor = cursor


level = main.Level([level_name])
cursor.load_objects(level.sprites)
main.level = level


changed_files_queue = queue.Queue()
file_monitoring_thread = threading.Thread(target=monitor_files_watchdog,
                                          args=(DIRECTORY_TO_MONITOR, changed_files_queue),
                                          daemon=True)
file_monitoring_thread.start()

current_level_name = level_name
activate_cursor = False

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                activate_cursor = not activate_cursor

    try:
        changed_file = changed_files_queue.get(block=False)
        logging.info(f"Измененный файл из очереди: {changed_file}")
        if changed_file == os.path.join(DIRECTORY_TO_MONITOR, current_level_name):
             update_level(level, changed_file, cursor)

        else:
            new_level_name = os.path.basename(changed_file)
            try:
                level.load(new_level_name)
                cursor.load_objects(level.sprites)
                current_level_name = new_level_name
                logging.info(f"Уровень переключен на {new_level_name}")
            except (IndexError, ValueError):
                level.load(current_level_name)
                cursor.load_objects(level.sprites)

    except queue.Empty:
        pass

    main.screen.fill((255, 255, 255))
    level.sprites.update()
    level.sprites.draw(main.screen)
    if activate_cursor:
        cursor_group.update()
    cursor_group.draw(main.screen)
    pygame.display.flip()
    main.clock.tick(60)
