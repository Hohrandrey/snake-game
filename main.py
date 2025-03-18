import curses
import signal
import sys
import time
import random
import os
import threading

# Глобальные переменные
direction = None
running = True
SAVE_FILE = "snake_save.txt"  # Файл для сохранения состояния
snake = []  # Список для хранения тела змейки
apple = None  # Координаты яблока
input_thread = None  # Поток для обработки ввода

def save_state():
    """Сохраняет текущее состояние игры в файл."""
    with open(SAVE_FILE, "w") as f:
        f.write(f"Direction: {direction}\n")
        f.write("Snake:\n")
        for y, x in snake:
            f.write(f"{y} {x}\n")
        f.write(f"Apple: {apple[0]} {apple[1]}\n")

def load_state():
    """Загружает состояние из текстового файла."""
    try:
        with open(SAVE_FILE, "r") as f:
            lines = f.readlines()
            direction = lines[0].strip().split(": ")[1]
            snake = []
            for line in lines[2:-1]:  # Читаем координаты змейки
                y, x = map(int, line.strip().split())
                snake.append([y, x])
            apple = list(map(int, lines[-1].strip().split(": ")[1].split()))
            return direction, snake, apple
    except FileNotFoundError:
        return "Вправо", [[0, 0]], [5, 5]  # Состояние по умолчанию

def create_apple(snake, height, width):
    """Создает новое яблоко, которое не находится на змейке."""
    while True:
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        if [y, x] not in snake:
            return [y, x]

def is_opposite(new_direction, current_direction):
    """Проверяет, является ли новое направление противоположным текущему."""
    opposites = {
        "Вверх": "Вниз",
        "Вниз": "Вверх",
        "Влево": "Вправо",
        "Вправо": "Влево",
    }
    return opposites.get(new_direction) == current_direction

def reset_game():
    """Сбрасывает игру на начальное состояние."""
    global direction, snake, apple
    direction = "Вправо"
    snake = [[0, 0]]  # Начальная позиция змейки
    apple = [5, 5]  # Начальная позиция яблока
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)  # Удаляем файл сохранения

def handle_exit(signum, frame):
    """Обрабатывает выход через Ctrl+C."""
    global running
    running = False
    print(f"\nПрограмма завершена. Направление: {direction}, Длина змейки: {len(snake)}")
    save_state()  # Сохраняем состояние перед выходом
    sys.exit(0)

def input_handler(stdscr):
    """Обрабатывает ввод пользователя в отдельном потоке."""
    global direction
    while running:
        key = stdscr.getch()
        new_direction = direction
        if key == curses.KEY_DOWN:
            new_direction = "Вниз"
        elif key == curses.KEY_UP:
            new_direction = "Вверх"
        elif key == curses.KEY_RIGHT:
            new_direction = "Вправо"
        elif key == curses.KEY_LEFT:
            new_direction = "Влево"
        elif key == ord('q'):  # Выход по нажатию 'q'
            handle_exit(None, None)
            break

        # Запрет на разворот
        if not is_opposite(new_direction, direction):
            direction = new_direction
        time.sleep(0.01)  # Небольшая задержка для снижения нагрузки на CPU

def main(stdscr):
    global direction, running, snake, apple, input_thread

    # Загружаем сохраненное состояние
    direction, snake, apple = load_state()

    # Настройка обработки Ctrl+C
    signal.signal(signal.SIGINT, handle_exit)

    curses.curs_set(0)  # Скрываем курсор
    stdscr.nodelay(True)  # Не блокировать ввод
    stdscr.keypad(True)  # Включаем поддержку специальных клавиш

    height, width = stdscr.getmaxyx()

    # Убедимся, что змейка и яблоко находятся в пределах экрана
    snake = [[y % height, x % width] for y, x in snake]
    apple = [apple[0] % height, apple[1] % width]

    # Запускаем поток для обработки ввода
    input_thread = threading.Thread(target=input_handler, args=(stdscr,))
    input_thread.start()

    # Основной цикл игры
    while running:
        # Вычисляем новую голову змейки
        head_y, head_x = snake[0]
        if direction == "Вниз":
            head_y = (head_y + 1) % height
        elif direction == "Вверх":
            head_y = (head_y - 1) % height
        elif direction == "Вправо":
            head_x = (head_x + 1) % width
        elif direction == "Влево":
            head_x = (head_x - 1) % width

        # Проверяем столкновение с собой
        if [head_y, head_x] in snake:
            print("\nИгра окончена! Змейка столкнулась с собой.")
            reset_game()  # Сбрасываем игру и удаляем файл сохранения
            continue  # Начинаем заново

        # Добавляем новую голову
        snake.insert(0, [head_y, head_x])

        # Проверяем, съела ли змейка яблоко
        if [head_y, head_x] == apple:
            apple = create_apple(snake, height, width)  # Создаем новое яблоко
        else:
            snake.pop()  # Удаляем хвост, если яблоко не съедено

        # Очистка экрана и отрисовка змейки и яблока
        stdscr.clear()
        for y, x in snake:
            stdscr.addch(y, x, '*')  # Тело змейки
        stdscr.addch(apple[0], apple[1], '@')  # Яблоко
        stdscr.refresh()

        # Разная задержка для горизонтального и вертикального движения
        if direction in ["Влево", "Вправо"]:
            time.sleep(0.05)  # Высокая скорость по горизонтали
        else:
            time.sleep(0.1)  # Обычная скорость по вертикали

    # Сохраняем состояние перед выходом
    save_state()

if __name__ == "__main__":
    curses.wrapper(main)