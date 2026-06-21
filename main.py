import pygame as pg
import random
import json

pg.init()
screen = pg.display.set_mode((800, 600))

#grid
CELL = 30
COLS = 10
ROWS = 20
GRID_W = COLS * CELL
GRID_H = ROWS * CELL

GRID = [[0 for _ in range(COLS)] for _ in range(ROWS)]

clock = pg.time.Clock()
font = pg.font.SysFont("consolas", 28)
LINE_SCORES = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}

SHAPES = {
    'I': [[0,0,0,0],
          [1,1,1,1],
          [0,0,0,0],
          [0,0,0,0]],
    'O': [[1,1],
          [1,1]],
    'T': [[0,1,0],
          [1,1,1],
          [0,0,0]],
    'L': [[0,0,1],
          [1,1,1],
          [0,0,0]],
    'J': [[1,0,0],
          [1,1,1],
          [0,0,0]],
    'S': [[0,1,1],
          [1,1,0],
          [0,0,0]],
    'Z': [[1,1,0],
          [0,1,1],
          [0,0,0]]
}

COLORS = {
    'I': (0, 240, 240),
    'O': (240, 240, 0),
    'T': (160, 0, 240),
    'L': (240, 160, 0),
    'J': (0, 0, 240),
    'S': (0, 240, 0),
    'Z': (240, 0, 0),
}

bag = []
font_small = pg.font.SysFont("consolas", 18)
HISCORE_FILE = "hiscore.json"
MAX_SCORES = 10
name_input = ""
NAME_MAX = 3

def load_hiscore():
    try:
        with open(HISCORE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return []
    

def save_hiscore(scores):
    with open(HISCORE_FILE, "w") as f:
        json.dump(scores, f)


def qualifies(scores, value):
    if value <= 0:
        return False
    if len(scores) < MAX_SCORES:
        return True
    return value > scores[-1]["score"]

def add_hiscore(scores, name, value, lines, lvl):
    scores.append({"name": name, "score": value, "lines": lines, "level": lvl})
    scores.sort(key=lambda e: e["score"], reverse=True)
    return scores[:MAX_SCORES]


def next_from_bag():
    global bag
    if not bag:
        bag = list(SHAPES.keys())
        random.shuffle(bag)
    return bag.pop()


def draw_grid(screen):
    for r in range(ROWS):
        for c in range(COLS):
            rect = pg.Rect(c * CELL, r * CELL, CELL, CELL)
            if GRID[r][c]:
                pg.draw.rect(screen, GRID[r][c], rect)
                pg.draw.rect(screen, (20, 20, 20), rect, 1)
            else:
                pg.draw.rect(screen, (40, 40, 40), rect, 1)


def draw_piece(screen, shape, color, px, py):
    for r in range(len(shape)):
        for c in range(len(shape[r])):
            if shape[r][c]:
                x = (px + c) * CELL
                y = (py + r) * CELL
                rect = pg.Rect(x, y, CELL, CELL)
                pg.draw.rect(screen, color, rect)
                pg.draw.rect(screen, (20, 20, 20), rect, 1)


def valid(shape, px, py):
    for r in range(len(shape)):
        for c in range(len(shape[r])):
            if shape[r][c]:
                col = px + c
                row = py + r
                if col < 0 or col >= COLS:
                    return False
                if row >= ROWS:
                    return False
                if row >= 0 and GRID[row][col] != 0:
                    return False
    return True


def lock_piece(shape, px, py, color):
    for r in range(len(shape)):
        for c in range(len(shape[r])):
            if shape[r][c]:
                GRID[py + r][px + c] = color


def new_piece():
    name = next_from_bag()
    return name, SHAPES[name], 3, 0


def clear_lines():
    global GRID
    new_grid = [row for row in GRID if any(cell == 0 for cell in row)]
    cleared = ROWS - len(new_grid)
    for _ in range(cleared):
        new_grid.insert(0, [0 for _ in range(COLS)])
    GRID = new_grid
    return cleared


def rotate(shape):
    return [list(row) for row in zip(*shape[::-1])]


def draw_score(screen, score, level, lines):
    items = [
        ("SCORE", str(score)),
        ("LEVEL", str(level)),
        ("LINES", str(lines)),
    ]
    y = 40
    for label_text, value_text in items:    
        label = font.render(label_text, True, (200, 200, 200))
        value = font.render(value_text, True, (255, 255, 255))
        screen.blit(label, (GRID_W + 30, y))
        screen.blit(value, (GRID_W + 30, y + 30))
        y += 75


def reset_game():
    global GRID, score, state, shape_name, shape, px, py, fall_time
    global next_name, hold_name, hold_used, level, lines_cleared, fall_speed
    global lock_timer, bag
    bag = []
    GRID = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    score = 0
    fall_time = 0
    state = "playing"
    level = 1
    lines_cleared = 0
    fall_speed = speed_for_level(1)
    shape_name, shape, px, py = new_piece()
    next_name = random.choice(list(SHAPES.keys()))
    hold_name = None
    hold_used = False
    lock_timer = 0


def lock_and_next():
    global shape_name, shape, px, py, score, state, next_name, fall_time, hold_used
    global level, lines_cleared, fall_speed, hiscores, name_input
    lock_piece(shape, px, py, COLORS[shape_name])
    cleared = clear_lines()
    score += LINE_SCORES[cleared] * level
    lines_cleared += cleared
    level = lines_cleared // 10 + 1
    fall_speed = speed_for_level(level)
    shape_name = next_name
    shape = SHAPES[shape_name]
    px, py = 3, 0
    next_name =  next_from_bag()
    hold_used = False
    if not valid(shape, px, py):
        if qualifies(hiscores, score):
            state = "enter_name"
            name_input = ""
        else:
            state = "game_over"


def draw_next(screen, name, ox, oy):
    label = font.render("Próxima", True, (200, 200, 200))
    screen.blit(label, (ox, oy))
    shape = SHAPES[name]
    color = COLORS[name]
    for r in range(len(shape)):
        for c in range(len(shape[r])):
            if shape[r][c]:
                x = ox + c * CELL
                y = oy + 30 + r * CELL
                rect = pg.Rect(x, y, CELL, CELL)
                pg.draw.rect(screen, color, rect)
                pg.draw.rect(screen, (20, 20, 20), rect, 1)


def hold_piece():
    global shape_name, shape, px, py, hold_name, next_name, hold_used
    if hold_used:
        return
    if hold_name is None:
        hold_name = shape_name
        shape_name = next_name
        next_name = random.choice(list(SHAPES.keys()))
    else:
        hold_name, shape_name = shape_name, hold_name
    shape = SHAPES[shape_name]
    px, py = 3, 0
    hold_used = True


def draw_hold(screen, name, ox, oy):
    label = font.render("Hold", True, (200, 200, 200))
    screen.blit(label, (ox, oy))
    if name is None:
        return
    shape = SHAPES[name]
    color = COLORS[name]
    for r in range(len(shape)):
        for c in range(len(shape[r])):
            if shape[r][c]:
                x = ox + c * CELL
                y = oy + 30 + r * CELL
                rect = pg.Rect(x, y, CELL, CELL)
                pg.draw.rect(screen, color, rect)
                pg.draw.rect(screen, (20, 20, 20), rect, 1)


def speed_for_level(level):
    return max(100, 500 - (level - 1) * 40)


def ghost_y(shape, px, py):
    gy = py
    while valid(shape, px, gy +1):
        gy += 1
    return gy


def draw_ghost(screen, shape, color, px, py):
    for r in range(len(shape)):
        for c in range(len(shape[r])):
            if shape[r][c]:
                x = (px + c) * CELL
                y = (py + r) * CELL
                rect = pg.Rect(x, y, CELL, CELL)
                pg.draw.rect(screen, color, rect, 2)


def draw_hiscores(screen, scores, ox, oy):
    title = font.render("Hiscores", True, (255, 215, 0))
    screen.blit(title, (ox, oy))
    
    header = f"{'#':<3} {'NOME':<7} {'PONTOS':>7} {'LEVEL':>3} {'LINHAS':>4}"
    head_txt = font_small.render(header, True, (120, 120, 120))
    screen.blit(head_txt, (ox, oy + 40))

    y = oy + 70
    for i, entry in enumerate(scores):
        rank = f"{i+1:<3}"
        name = entry["name"][:6].ljust(7)
        sc = str(entry["score"]).rjust(7)
        lv = str(entry["level"]).rjust(3)
        ln = str(entry["lines"]).rjust(4)
        line = f"{rank}{name}{sc} {lv} {ln}"
        color = (255, 255, 255) if i < 3 else (170, 170, 170)
        txt = font_small.render(line, True, color)
        screen.blit(txt, (ox, y))
        y += 26


LOCK_DELAY = 500
DAS_DELAY = 130
DAS_RATE = 40
das_dir = 0
das_timer = 0
das_charged = False
on_ground = False
running = True
paused = False
state = "playing"
hiscores = load_hiscore()
reset_game()
while running:
    for event in pg.event.get():
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_p and not state == "playing":
                paused = not paused
            elif state == "game_over":
                if event.key == pg.K_r:
                    reset_game()
            elif state == "enter_name":
                if event.key == pg.K_RETURN:
                    final_name = name_input if name_input else "AAA"
                    hiscores = add_hiscore(hiscores, final_name, score, lines_cleared, level)
                    save_hiscore(hiscores)
                    state = "game_over"
                elif event.key == pg.K_BACKSPACE:
                    name_input = name_input[:-1]
                elif len(name_input) < NAME_MAX and event.unicode.isalnum():
                    name_input += event.unicode.upper()
            elif state == "playing" and not paused:
                if event.key == pg.K_LEFT:
                    if valid(shape, px - 1, py):
                        px -= 1
                        lock_timer = 0
                    das_dir = -1
                    das_timer = 0
                    das_charged = False
                elif event.key == pg.K_RIGHT:
                    if valid(shape, px + 1, py):
                        px += 1
                        lock_timer = 0
                    das_dir = 1
                    das_timer = 0
                    das_charged = False
                elif event.key == pg.K_DOWN:
                    if valid(shape, px, py + 1):
                        py += 1
                        lock_timer = 0
                elif event.key == pg.K_UP:
                    rotated = rotate(shape)
                    for dx, dy in [(0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1)]:
                        if valid(rotated, px + dx, py + dy):
                            shape = rotated
                            px += dx
                            py += dy
                            lock_timer = 0
                            break
                elif event.key == pg.K_SPACE:
                    while valid(shape, px, py + 1):
                        py += 1
                    lock_and_next()
                    fall_time = 0
                    lock_timer = 0
                elif event.key == pg.K_c:
                    hold_piece()
        if event.type == pg.KEYUP:
            if event.key == pg.K_LEFT and das_dir == -1:
                das_dir = 0
            elif event.key == pg.K_RIGHT and das_dir == 1:
                das_dir = 0
        if event.type == pg.QUIT:
            running = False
        
    screen.fill((0, 0, 0))
    draw_grid(screen)
    gy = ghost_y(shape, px, py)
    ghost_color = tuple(c // 3 for c in COLORS[shape_name])
    draw_ghost(screen, shape, ghost_color, px, gy)
    draw_piece(screen, shape, COLORS[shape_name], px, py)
    draw_score(screen, score, level, lines_cleared)
    draw_next(screen, next_name, GRID_W + 30, 300)
    draw_hold(screen, hold_name, GRID_W + 30, 440)
    draw_hiscores(screen, hiscores, GRID_W + 160, 40)
    
    if state == "enter_name":
        msg = font.render("Novo recorde!", True, (255, 215, 0))
        prompt = font.render("Nome: " + name_input + "_", True, (255, 255, 255))
        cx = GRID_W // 2
        screen.blit(msg, (cx - msg.get_width() // 2, ROWS * CELL // 2 - 50))
        screen.blit(prompt, (cx - prompt.get_width() // 2, ROWS * CELL // 2))
        
    if state == "game_over":
        over = font.render("GAME OVER", True, (255, 80, 80))
        hint = font.render("Pressione R para reiniciar", True, (200, 200, 200))
        screen.blit(over, (GRID_W // 2 - over.get_width() // 2, ROWS * CELL // 2 - 50))
        screen.blit(hint, (GRID_W // 2 - hint.get_width() // 2, ROWS * CELL // 2))
    
    if paused:
        pause_txt = font.render("PAUSADO", True, (255, 255, 255))
        screen.blit(pause_txt, (GRID_W // 2 - pause_txt.get_width() // 2, ROWS * CELL // 2))
    
    pg.display.flip()
    dt = clock.tick(60)
    if state == "playing" and not paused:
        if das_dir != 0:
            das_timer += dt
            if not das_charged:
                if das_timer >= DAS_DELAY:
                    das_charged = True
                    das_timer = 0
            else:
                while das_timer >= DAS_RATE:
                    das_timer -= DAS_RATE
                    if valid(shape, px + das_dir, py):
                        px += das_dir
                        lock_timer = 0
                    else:
                        break
        on_ground = not valid(shape, px, py + 1)

        if on_ground:
            lock_timer += dt
            if lock_timer >= LOCK_DELAY:
                lock_and_next()
                fall_time = 0
                lock_timer = 0
        else:
            lock_timer = 0
            fall_time += dt
            if fall_time >= fall_speed:
                if valid(shape, px, py + 1):
                    py += 1
                fall_time = 0

pg.quit()
