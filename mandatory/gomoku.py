from board import *

import pygame
import sys
import time
import random
import math

from ai import get_move

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

BOARD_SIZE   = 19          # 19×19 intersections
CELL         = 42          # pixels between intersections
MARGIN       = 48          # pixels from window edge to first/last line
BOARD_PX     = MARGIN * 2 + CELL * (BOARD_SIZE - 1)   # board canvas size

PANEL_W      = 260         # right-side info panel width
WIN_W        = BOARD_PX + PANEL_W
WIN_H        = BOARD_PX

FPS          = 60

# Colours
C_WOOD_DARK  = (182, 130,  60)   # grid lines / border
C_WOOD_LIGHT = (220, 175,  90)   # board fill
C_WOOD_BG    = (200, 150,  70)   # board face
C_PANEL_BG   = ( 30,  28,  24)   # right panel
C_PANEL_LINE = ( 70,  65,  55)   # panel dividers
C_WHITE_STONE= (245, 245, 238)
C_BLACK_STONE= ( 22,  22,  22)
C_STONE_SHD  = ( 80,  60,  20)   # shadow under stones
C_TEXT_HI    = (255, 220, 100)   # highlighted text
C_TEXT_LO    = (190, 180, 160)   # muted text
C_TEXT_WHITE = (240, 235, 225)
C_SUGGEST    = (255, 220,   0)   # move suggestion ring
C_LAST_MOVE  = (255,  80,  80)   # small dot on last move
C_MSG_ERR    = (255,  90,  70)
C_MSG_OK     = (120, 220, 120)
C_WIN_BG     = ( 10,  10,  10, 200)  # semi-transparent win overlay


# Players
BLACK = 1
WHITE = 2

# Game modes
MODE_HvAI = 1
MODE_HvH  = 2
MODE_AIvAI = 3  


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: board coordinate ↔ pixel coordinate
# ─────────────────────────────────────────────────────────────────────────────

def board_to_px(row, col):
    """Return pixel centre of intersection (row, col)."""
    x = MARGIN + col * CELL
    y = MARGIN + row * CELL
    return x, y


def px_to_board(px, py):
    """
    Convert pixel position (px, py) to the nearest board intersection.
    Returns (row, col) or None if the click is too far from any intersection.
    """
    col = round((px - MARGIN) / CELL)
    row = round((py - MARGIN) / CELL)
    if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
        return None
    # Reject clicks that are more than half a cell away
    cx, cy = board_to_px(row, col)
    if abs(px - cx) <= CELL // 2 and abs(py - cy) <= CELL // 2:
        return row, col
    return None


# ─────────────────────────────────────────────────────────────────────────────
# WIN DETECTION (alignment only — capture win checked in game loop)
# ─────────────────────────────────────────────────────────────────────────────

def check_alignment_win(board, row, col, player):
    """
    Returns True if placing at (row, col) gives `player` 5 or more in a row
    in any of the four directions.
    """
    directions = [(0,1),(1,0),(1,1),(1,-1)]
    for dr, dc in directions:
        count = 1
        for sign in (1, -1):
            r, c = row + sign*dr, col + sign*dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
                count += 1
                r += sign*dr
                c += sign*dc
        if count >= 5:
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# DRAWING FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def draw_board(surface):
    """Draw the wooden Goban: background, grid lines, and star points."""
    # Wood background with a subtle radial gradient effect via concentric rects
    surface.fill(C_WOOD_BG)
    for i in range(12):
        shade = max(0, 15 - i * 1)
        r = pygame.Rect(i*2, i*2, BOARD_PX - i*4, BOARD_PX - i*4)
        pygame.draw.rect(surface, (
            min(255, C_WOOD_LIGHT[0] - shade),
            min(255, C_WOOD_LIGHT[1] - shade),
            min(255, C_WOOD_LIGHT[2] - shade),
        ), r, 2)

    # Grid lines
    for i in range(BOARD_SIZE):
        x = MARGIN + i * CELL
        y = MARGIN + i * CELL
        pygame.draw.line(surface, C_WOOD_DARK, (MARGIN, y), (MARGIN + (BOARD_SIZE-1)*CELL, y), 1)
        pygame.draw.line(surface, C_WOOD_DARK, (x, MARGIN), (x, MARGIN + (BOARD_SIZE-1)*CELL), 1)

    # Border (thicker outer lines)
    pygame.draw.rect(surface, C_WOOD_DARK,
        (MARGIN, MARGIN, (BOARD_SIZE-1)*CELL, (BOARD_SIZE-1)*CELL), 2)



def draw_stone(surface, row, col, player, alpha=255):
    """Draw a single stone (black or white) at the given intersection."""
    cx, cy = board_to_px(row, col)
    radius = CELL // 2 - 3

    # Shadow
    shadow_surf = pygame.Surface((radius*2+6, radius*2+6), pygame.SRCALPHA)
    pygame.draw.circle(shadow_surf, (*C_STONE_SHD, 100),
                       (radius+5, radius+5), radius)
    surface.blit(shadow_surf, (cx - radius - 2, cy - radius - 2))

    color = C_BLACK_STONE if player == BLACK else C_WHITE_STONE
    pygame.draw.circle(surface, color, (cx, cy), radius)

    # Highlight glint
    glint_color = (80, 80, 80) if player == BLACK else (255, 255, 255)
    glint_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    pygame.draw.ellipse(glint_surf, (*glint_color, 70),
                        (radius//3, radius//5, radius//2, radius//3))
    surface.blit(glint_surf, (cx - radius, cy - radius))

    # Thin border for white stones so they're visible on wood
    if player == WHITE:
        pygame.draw.circle(surface, (160, 150, 130), (cx, cy), radius, 1)


def draw_all_stones(surface, board, last_move=None, suggestion=None):
    """Redraw every stone on the board, plus last-move marker and suggestion."""
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0:
                draw_stone(surface, r, c, board[r][c])

    # Small red dot on the last placed stone
    if last_move:
        lr, lc = last_move
        cx, cy = board_to_px(lr, lc)
        pygame.draw.circle(surface, C_LAST_MOVE, (cx, cy), 4)

    # Yellow suggestion ring (hotseat mode)
    if suggestion:
        sr, sc = suggestion
        cx, cy = board_to_px(sr, sc)
        pygame.draw.circle(surface, C_SUGGEST, (cx, cy), CELL//2 - 3, 3)


def draw_panel(surface, fonts, state):
    """
    Draw the right-side info panel showing:
      - Game mode
      - Whose turn it is
      - Capture counters
      - AI move timer
      - Last status message
      - Win announcement
    `state` is the GameState object.
    """
    panel_rect = pygame.Rect(BOARD_PX, 0, PANEL_W, WIN_H)
    pygame.draw.rect(surface, C_PANEL_BG, panel_rect)

    f_title  = fonts['title']
    f_body   = fonts['body']
    f_small  = fonts['small']
    f_big    = fonts['big']

    x = BOARD_PX + 20
    y = 28

    # ── Title ──
    title = surface.blit(f_title.render("GOMOKU", True, C_TEXT_HI), (x, y))
    y += title.height + 4
    # mode_name = "Human vs AI" if state.mode == MODE_HvAI else "Hotseat"
    if state.mode == MODE_HvAI:
        mode_name = "Human vs AI"
    elif state.mode == MODE_HvH:
        mode_name = "Hotseat"
    else:
        mode_name = "AI vs AI"
    surface.blit(f_small.render(mode_name, True, C_TEXT_LO), (x, y))
    y += 28

    # Divider
    pygame.draw.line(surface, C_PANEL_LINE,
                     (BOARD_PX + 12, y), (BOARD_PX + PANEL_W - 12, y), 1)
    y += 16

    # ── Turn indicator ──
    if not state.game_over:
        name  = "Black" if state.current_player == BLACK else "White"
        color = (50, 50, 50) if state.current_player == BLACK else (230, 230, 210)
        # Small stone icon
        pygame.draw.circle(surface, color, (x + 10, y + 10), 10)
        if state.current_player == WHITE:
            pygame.draw.circle(surface, (150, 140, 120), (x + 10, y + 10), 10, 1)
        label = f_body.render(f"  {name}'s turn", True, C_TEXT_WHITE)
        surface.blit(label, (x + 12, y + 2))
    y += 36

    # Divider
    pygame.draw.line(surface, C_PANEL_LINE,
                     (BOARD_PX + 12, y), (BOARD_PX + PANEL_W - 12, y), 1)
    y += 18

    # ── Capture counters ──
    surface.blit(f_small.render("CAPTURES", True, C_TEXT_LO), (x, y))
    y += 22

    # Black captures
    pygame.draw.circle(surface, C_BLACK_STONE, (x + 10, y + 10), 9)
    bc_txt = f_body.render(f"  Black:  {state.cap_black:2d} / 10", True, C_TEXT_WHITE)
    surface.blit(bc_txt, (x + 12, y + 1))
    y += 32

    # White captures
    pygame.draw.circle(surface, C_WHITE_STONE, (x + 10, y + 10), 9)
    pygame.draw.circle(surface, (150, 140, 120), (x + 10, y + 10), 9, 1)
    wc_txt = f_body.render(f"  White:  {state.cap_white:2d} / 10", True, C_TEXT_WHITE)
    surface.blit(wc_txt, (x + 12, y + 1))
    y += 38

    # Divider
    pygame.draw.line(surface, C_PANEL_LINE,
                     (BOARD_PX + 12, y), (BOARD_PX + PANEL_W - 12, y), 1)
    y += 18

    # ── AI Move Timer ──
    surface.blit(f_small.render("AI MOVE TIMER", True, C_TEXT_LO), (x, y))
    y += 22
    timer_ms = state.ai_move_time_ms
    if timer_ms is None:
        timer_str = "—"
        timer_color = C_TEXT_LO
    else:
        timer_str = f"{timer_ms:.1f} ms"
        timer_color = C_MSG_OK if timer_ms < 500 else C_MSG_ERR
    timer_surf = f_big.render(timer_str, True, timer_color)
    surface.blit(timer_surf, (x, y))
    y += timer_surf.get_height() + 6

    # Warning if over 500 ms
    if timer_ms and timer_ms >= 500:
        warn = f_small.render("⚠ AI too slow (>500 ms)", True, C_MSG_ERR)
        surface.blit(warn, (x, y))
        y += 20
    y += 10

    # Divider
    pygame.draw.line(surface, C_PANEL_LINE,
                     (BOARD_PX + 12, y), (BOARD_PX + PANEL_W - 12, y), 1)
    y += 18

    # ── Suggestion note (hotseat) ──
    if state.mode == MODE_HvH and state.suggestion:
        sr, sc = state.suggestion
        sg_txt = f_small.render(
            f"Suggestion: ({sr},{sc})", True, C_SUGGEST)
        surface.blit(sg_txt, (x, y))
        y += 22
        hint = f_small.render("(yellow ring on board)", True, C_TEXT_LO)
        surface.blit(hint, (x, y))
        y += 28

    # Divider
    pygame.draw.line(surface, C_PANEL_LINE,
                     (BOARD_PX + 12, y), (BOARD_PX + PANEL_W - 12, y), 1)
    y += 18

    # ── Status message ──
    if state.status_msg:
        msg_color = C_MSG_ERR if state.status_is_error else C_MSG_OK
        for line in _wrap(state.status_msg, f_small, PANEL_W - 32):
            surface.blit(f_small.render(line, True, msg_color), (x, y))
            y += 20
    y += 10

    # ── Win overlay ──
    if state.game_over:
        _draw_win_overlay(surface, fonts, state.win_message)

    # ── Key hints at bottom ──
    hints = [
        "R  –  restart",
        "Q  –  quit",
    ]
    hy = WIN_H - 14 - len(hints) * 18
    for hint in hints:
        surface.blit(f_small.render(hint, True, C_TEXT_LO), (x, hy))
        hy += 18


def _draw_win_overlay(surface, fonts, message):
    """Semi-transparent banner across the board announcing the winner."""
    overlay = pygame.Surface((BOARD_PX, 100), pygame.SRCALPHA)
    overlay.fill((10, 10, 10, 210))
    surface.blit(overlay, (0, BOARD_PX // 2 - 50))
    pygame.draw.rect(surface, C_TEXT_HI,
                     (0, BOARD_PX // 2 - 50, BOARD_PX, 100), 3)

    f = fonts['win']
    lines = message.split('\n')
    total_h = len(lines) * (f.get_height() + 4)
    start_y = BOARD_PX // 2 - total_h // 2
    for line in lines:
        surf = f.render(line, True, C_TEXT_HI)
        surface.blit(surf, (BOARD_PX // 2 - surf.get_width() // 2, start_y))
        start_y += f.get_height() + 4


def _wrap(text, font, max_width):
    """Simple word-wrap: returns list of lines that fit within max_width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


# ─────────────────────────────────────────────────────────────────────────────
# MODE SELECTION SCREEN
# ─────────────────────────────────────────────────────────────────────────────

def draw_mode_screen(surface, fonts):
    """Render the opening mode-select screen."""
    surface.fill((20, 18, 14))

    f_title = fonts['title']
    f_body  = fonts['body']
    f_small = fonts['small']

    cx = WIN_W // 2

    # Title
    t = fonts['win'].render("GOMOKU", True, C_TEXT_HI)
    surface.blit(t, (cx - t.get_width() // 2, 80))

    sub = f_body.render("Select game mode", True, C_TEXT_LO)
    surface.blit(sub, (cx - sub.get_width() // 2, 160))

    # Mode buttons (drawn as rounded rects)
    options = [
        ("1", "Human vs AI",    "Play against the Minimax engine"),
        ("2", "Hotseat (HvH)",  "Two players, with AI move suggestions"),
        ("3", "AI vs AI",       "Watch two AI engines play each other"),
    ]
    for i, (key, label, desc) in enumerate(options):
        ry = 210 + i * 100
        rect = pygame.Rect(cx - 180, ry, 360, 80)
        pygame.draw.rect(surface, (40, 36, 28), rect, border_radius=10)
        pygame.draw.rect(surface, C_WOOD_DARK, rect, 2, border_radius=10)

        key_surf = fonts['big'].render(f"[{key}]", True, C_TEXT_HI)
        surface.blit(key_surf, (rect.x + 18, ry + 10))

        lbl_surf = f_body.render(label, True, C_TEXT_WHITE)
        surface.blit(lbl_surf, (rect.x + 18, ry + 40))

        dsc_surf = f_small.render(desc, True, C_TEXT_LO)
        surface.blit(dsc_surf, (rect.x + 18, ry + 60))

    hint = f_small.render("Press 1, 2 or 3 to begin", True, C_TEXT_LO)
    surface.blit(hint, (cx - hint.get_width() // 2, WIN_H - 60))

# ─────────────────────────────────────────────────────────────────────────────
# GAME STATE
# ─────────────────────────────────────────────────────────────────────────────

class GameState:
    """Holds all mutable state for an in-progress game."""

    def __init__(self, mode):
        self.mode           = mode
        self.board          = [[0]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_player = BLACK          
        self.cap_black      = 0             # stones captured BY black
        self.cap_white      = 0             # stones captured BY white
        self.game_over      = False
        self.win_message    = ""
        self.last_move      = None           # (row, col)
        self.suggestion     = None           # (row, col) for hotseat hint
        self.ai_move_time_ms= None           # float ms
        self.status_msg     = ""
        self.status_is_error= False
        # self.ai_player      = WHITE if mode == MODE_HvAI else None
        if mode == MODE_HvAI:
            self.ai_player = WHITE
        elif mode == MODE_AIvAI:
            self.ai_player = "both"
        else:
            self.ai_player = None
        self.waiting_for_ai = False


    def set_status(self, msg, error=False):
        self.status_msg      = msg
        self.status_is_error = error



    def place_stone(self, row, col):
        """
        Attempt to place the current player's stone at (row, col).
        Returns True on success, False if the move was blocked.
        Handles captures, win detection, and turn switching.
        """
        player = self.current_player
        opponent = WHITE if player == BLACK else BLACK
        # ── Validate move ──
        if self.board[row][col] != 0:
            self.set_status("Cell already occupied.", error=True)
            return False

        if is_move_into_capture(self.board, row, col, player):
            self.set_status("You can't move into a capture.", error=True)
            return False
        # count = count_free_threes(self.board, row, col, player)

        if is_double_three(self.board, row, col, player): ####
            # check capture exception
            temp = [r[:] for r in self.board]
            temp[row][col] = player
            captured_temp = apply_captures(temp, row, col, player)
            if not captured_temp:
                self.set_status("Double-three is forbidden.", error=True)
                return False

        # ── Place the stone ──
        self.board[row][col] = player
        self.last_move = (row, col)
        self.status_msg = ""

        # ── Apply captures ── ####
        captured = apply_captures(self.board, row, col, player)
        if player == BLACK:
            self.cap_black += len(captured)
        else:
            self.cap_white += len(captured)

        # ── Win by capture ── #! logic not implimented yet
        if self.cap_black >= 10:
            self._win("Black wins by capture!\n(10 stones captured)")
            return True
        if self.cap_white >= 10:
            self._win("White wins by capture!\n(10 stones captured)")
            return True

        # ── Win by alignment (with endgame capture check) ──
        if check_alignment_win(self.board, row, col, player):
            alignment = get_alignment_stones(self.board, row, col, player)
            opp_caps  = self.cap_white if player == BLACK else self.cap_black
            if not can_capture_alignment(self.board, alignment, opponent):
                name = "Black" if player == BLACK else "White"
                self._win(f"{name} wins!\n5 in a row!")
                return True
            elif opp_caps >= 8:
                name = "Black" if opponent == BLACK else "White"
                self._win(f"{name} wins by capture!\n(broke the alignment)")
                return True
            # else game continues — alignment can be broken

        # ── Switch turn ──
        self.current_player = WHITE if player == BLACK else BLACK
        return True


    def _win(self, message):
        self.game_over   = True
        self.win_message = message
        self.set_status(message)


# ─────────────────────────────────────────────────────────────────────────────
# AI TURN (runs in main thread; replace with threading if needed)
# ─────────────────────────────────────────────────────────────────────────────

# def run_ai_turn(state, surface, fonts, clock): #! this is only to test the timer display not the actual AI move
#     state.waiting_for_ai = True
#     start = time.perf_counter()

#     placed = False
#     while not placed:
#         clock.tick(FPS)
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 pygame.quit(); sys.exit()

#             elif event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE):
#                 pygame.quit(); sys.exit()

#             elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
#                 pos = px_to_board(*event.pos)
#                 if pos is None:
#                     state.set_status("Click closer to an intersection.", error=True)
#                     continue

#                 row, col = pos
#                 if state.place_stone(row, col):
#                     placed = True

#         redraw(surface, fonts, state)
#         pygame.display.flip()

#     state.ai_move_time_ms = (time.perf_counter() - start) * 1000
#     state.waiting_for_ai = False

def run_ai_turn(state, surface, fonts, clock):
    state.waiting_for_ai = True
    redraw(surface, fonts, state)
    pygame.display.flip()

    start = time.perf_counter()
    row, col = get_move(
        state.board,
        state.current_player,
        {BLACK: state.cap_black, WHITE: state.cap_white}
    )
    state.ai_move_time_ms = (time.perf_counter() - start) * 1000

    state.place_stone(row, col)
    state.waiting_for_ai = False

def run_suggestion(state):
    #! suggestion logic to be iplimented 
    pass


# ─────────────────────────────────────────────────────────────────────────────
# FULL REDRAW
# ─────────────────────────────────────────────────────────────────────────────

def redraw(surface, fonts, state):
    """Composite the entire frame: board + stones + panel."""
    draw_board(surface)
    draw_all_stones(surface, state.board,
                    last_move=state.last_move,
                    suggestion=state.suggestion if state.mode == MODE_HvH else None)
    draw_panel(surface, fonts, state)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    pygame.display.set_caption("Gomoku")

    surface = pygame.display.set_mode((WIN_W, WIN_H))
    clock   = pygame.time.Clock()

    # ── Fonts ──
    try:
        fonts = {
            'title': pygame.font.SysFont("Georgia",       26, bold=True),
            'body':  pygame.font.SysFont("Georgia",       18),
            'small': pygame.font.SysFont("Courier",       13),
            'big':   pygame.font.SysFont("Georgia",       22, bold=True),
            'win':   pygame.font.SysFont("Georgia",       30, bold=True),
        }
    except Exception:
        f = pygame.font.Font(None, 24)
        fonts = {k: f for k in ('title','body','small','big','win')}

    # ── Mode selection ──
    mode = None
    while mode is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    mode = MODE_HvAI
                elif event.key == pygame.K_2:
                    mode = MODE_HvH
                elif event.key == pygame.K_3:
                    mode = MODE_AIvAI
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit(); sys.exit()
        
        draw_mode_screen(surface, fonts)
        pygame.display.flip()
        clock.tick(FPS)

    # ── Game initialisation ──
    state = GameState(mode)

    # ── If AI vs AI, start playing immediately ──          ← ADD (block A)
    if state.mode == MODE_AIvAI:                             # ← ADD
        redraw(surface, fonts, state)                        # ← ADD
        pygame.display.flip()                                # ← ADD
        run_ai_turn(state, surface, fonts, clock)            # ← ADD
        pygame.time.wait(300)                                # ← ADD

    # ── Main game loop ──
    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False

                elif event.key == pygame.K_r:
                    # Restart: go back to mode select
                    mode = None
                    while mode is None:
                        for ev2 in pygame.event.get():
                            if ev2.type == pygame.QUIT:
                                pygame.quit(); sys.exit()
                            if ev2.type == pygame.KEYDOWN:
                                if ev2.key == pygame.K_1:
                                    mode = MODE_HvAI
                                elif ev2.key == pygame.K_2:
                                    mode = MODE_HvH
                                elif ev2.key == pygame.K_3:
                                    mode = MODE_AIvAI
                                elif ev2.key in (pygame.K_q, pygame.K_ESCAPE):
                                    pygame.quit(); sys.exit()
                        draw_mode_screen(surface, fonts)
                        pygame.display.flip()
                        clock.tick(FPS)
                    state = GameState(mode)


            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state.game_over:
                    continue

                
                if state.mode == MODE_AIvAI:
                    continue

                # In HvAI mode, ignore clicks when it is the AI's turn
                if state.mode == MODE_HvAI and state.current_player == state.ai_player:
                    continue

                pos = px_to_board(*event.pos)
                if pos is None:
                    state.set_status("Click closer to an intersection.", error=True)
                    continue


                row, col = pos
                success = state.place_stone(row, col)

                if success and not state.game_over:
                    # HvAI: trigger AI response
                    if state.mode == MODE_HvAI and state.current_player == state.ai_player:
                        redraw(surface, fonts, state)
                        pygame.display.flip()
                        run_ai_turn(state, surface, fonts, clock)

                    # Hotseat: compute suggestion for the next player
                    elif state.mode == MODE_HvH:
                        state.suggestion = None
                        redraw(surface, fonts, state)
                        pygame.display.flip()
                        run_suggestion(state)

        # ── Draw ──
        redraw(surface, fonts, state)
        pygame.display.flip()

        # ── AI vs AI keeps playing automatically ──     
        if state.mode == MODE_AIvAI and not state.game_over:
            run_ai_turn(state, surface, fonts, clock)
            pygame.time.wait(300)       


    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()