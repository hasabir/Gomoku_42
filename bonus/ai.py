from constant import *
from board import *
import random

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

MAX_DEPTH = 10

WIN_SCORE      = 10_000_000
LOSE_SCORE     = -10_000_000

# ─────────────────────────────────────────────────────────────────────────────
# CANDIDATE MOVES
# ─────────────────────────────────────────────────────────────────────────────

def get_candidates(board):
    occupied = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                occupied.append((r, c))

    if not occupied:
        return [(9, 9)]

    candidates = set()
    for r, c in occupied:
        for dr in range(-1, 2):        # radius 1
            for dc in range(-1, 2):
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if board[nr][nc] == EMPTY:
                        candidates.add((nr, nc))
    return list(candidates)
# ─────────────────────────────────────────────────────────────────────────────
# HEURISTIC
# ─────────────────────────────────────────────────────────────────────────────

# Pattern scores
SCORES = {
    5: WIN_SCORE,    # 5 in a row — win
    4: 100_000,      # open four
    3: 10_000,       # open three
    2: 1_000,        # open two
    1: 100,          # single stone
}

def evaluate_line(line, player):
    """
    Score a single line (list of cell values).
    Counts consecutive player stones and checks if ends are open.
    """
    opponent = WHITE if player == BLACK else BLACK
    score = 0
    n = len(line)
    i = 0

    while i < n:
        if line[i] == player:
            # count consecutive stones
            count = 0
            j = i
            while j < n and line[j] == player:
                count += 1
                j += 1

            # check open ends
            left_open  = (i > 0 and line[i-1] == EMPTY)
            right_open = (j < n and line[j] == EMPTY)
            open_ends  = (1 if left_open else 0) + (1 if right_open else 0)

            if count >= 5:
                score += WIN_SCORE
            elif open_ends == 2:
                score += SCORES.get(count, 0) * 2   # fully open — double score
            elif open_ends == 1:
                score += SCORES.get(count, 0)        # half open
            # open_ends == 0 → blocked on both sides → worthless

            i = j
        else:
            i += 1

    return score


def get_all_lines(board):
    """Extract all rows, columns, and diagonals from the board."""
    lines = []

    # rows
    for r in range(BOARD_SIZE):
        lines.append([board[r][c] for c in range(BOARD_SIZE)])

    # columns
    for c in range(BOARD_SIZE):
        lines.append([board[r][c] for r in range(BOARD_SIZE)])

    # diagonals top-left to bottom-right
    for start in range(-(BOARD_SIZE-5), BOARD_SIZE-4):
        line = []
        for i in range(BOARD_SIZE):
            r, c = i, i - start
            if 0 <= c < BOARD_SIZE:
                line.append(board[r][c])
        if len(line) >= 5:
            lines.append(line)

    # diagonals top-right to bottom-left
    for start in range(4, BOARD_SIZE*2 - 4):
        line = []
        for i in range(BOARD_SIZE):
            r, c = i, start - i
            if 0 <= c < BOARD_SIZE:
                line.append(board[r][c])
        if len(line) >= 5:
            lines.append(line)

    return lines


def evaluate(board, ai_player, captures):
    """
    Score the board from `player`'s perspective.
    Positive = good for player, negative = bad.
    """
    opponent = WHITE if ai_player == BLACK else BLACK
    score = 0

    # only scan lines through occupied cells — much faster
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0:
                for dr, dc in [(0,1),(1,0),(1,1),(1,-1)]:
                    score += score_direction(board, r, c, dr, dc, ai_player)
                    score -= score_direction(board, r, c, dr, dc, opponent)

    my_caps  = captures[ai_player]
    opp_caps = captures[opponent]
    score += my_caps  * 500
    score -= opp_caps * 500

    return score

def score_direction(board, r, c, dr, dc, player):
    """Score a sequence starting at (r,c) going in (dr,dc)."""
    if board[r][c] != player:
        return 0

    # only score from the start of a sequence to avoid counting twice
    prev_r, prev_c = r - dr, c - dc
    if (0 <= prev_r < BOARD_SIZE and 0 <= prev_c < BOARD_SIZE
            and board[prev_r][prev_c] == player):
        return 0  # not the start of this sequence

    # count the sequence
    count = 0
    i, j = r, c
    while 0 <= i < BOARD_SIZE and 0 <= j < BOARD_SIZE and board[i][j] == player:
        count += 1
        i += dr
        j += dc

    if count == 0:
        return 0

    # check open ends
    left_open  = (0 <= r-dr < BOARD_SIZE and 0 <= c-dc < BOARD_SIZE
                  and board[r-dr][c-dc] == 0)
    right_open = (0 <= i < BOARD_SIZE and 0 <= j < BOARD_SIZE
                  and board[i][j] == 0)
    open_ends  = (1 if left_open else 0) + (1 if right_open else 0)

    if count >= 5:
        return WIN_SCORE
    elif open_ends == 2:
        return SCORES.get(count, 0) * 2
    elif open_ends == 1:
        return SCORES.get(count, 0)
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# MINIMAX WITH ALPHA-BETA
# ─────────────────────────────────────────────────────────────────────────────

def minimax(board, depth, alpha, beta, maximizing, ai_player, captures, start=None, time_limit=None):
    """
    Returns (score, move) where move is (row, col) or None at leaf nodes.
    ai_player  — the player the AI is playing as
    maximizing — True when it's the AI's turn, False when opponent's turn
    """
    if start and time_limit and time.perf_counter() - start > time_limit:
        return evaluate(board, ai_player, captures), None

    if depth == 0:
        return evaluate(board, ai_player, captures), None


    current_player = ai_player if maximizing else (WHITE if ai_player == BLACK else BLACK)

    # ── Terminal: depth reached ──
    if depth == 0:
        return evaluate(board, ai_player, captures), None

    candidates = get_candidates(board)

    # ── Terminal: no moves ──
    if not candidates:
        return evaluate(board, ai_player, captures), None

    best_move = None

    if maximizing:
        best_score = LOSE_SCORE
        for r, c in order_moves(candidates, board, current_player, captures):
            legal, _ = is_legal_move(board, r, c, current_player)
            if not legal:
                continue

            # simulate move
            board[r][c] = current_player
            captured = apply_captures(board, r, c, current_player)
            new_captures = dict(captures)
            new_captures[current_player] += len(captured)

            # check terminal win
            if new_captures[current_player] >= 10 or check_alignment(board, r, c, current_player):
                score = WIN_SCORE + depth  # prefer faster wins
            else:
                score, _ = minimax(board, depth-1, alpha, beta, False, ai_player, new_captures, start, time_limit)

            # undo move
            board[r][c] = EMPTY
            for cr, cc in captured:
                board[cr][cc] = current_player  # restore captured stones

            if score > best_score:
                best_score = score
                best_move  = (r, c)

            alpha = max(alpha, best_score)
            if beta <= alpha:
                break  # ── prune ──

        return best_score, best_move

    else:
        best_score = WIN_SCORE
        for r, c in order_moves(candidates, board, current_player, captures):
            legal, _ = is_legal_move(board, r, c, current_player)
            if not legal:
                continue

            # simulate move
            board[r][c] = current_player
            captured = apply_captures(board, r, c, current_player)
            new_captures = dict(captures)
            new_captures[current_player] += len(captured)

            # check terminal loss
            if new_captures[current_player] >= 10 or check_alignment(board, r, c, current_player):
                score = LOSE_SCORE - depth  # prefer slower losses
            else:
                score, _ = minimax(board, depth-1, alpha, beta, True, ai_player, new_captures, start, time_limit)

            # undo move
            board[r][c] = EMPTY
            for cr, cc in captured:
                board[cr][cc] = current_player

            if score < best_score:
                best_score = score
                best_move  = (r, c)

            beta = min(beta, best_score)
            if beta <= alpha:
                break  # ── prune ──

        return best_score, best_move


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
import time

TIME_LIMIT = 0.45

def get_move(board, player, captures, max_depth=MAX_DEPTH, opening="standard", move_num=1):
    board_copy = copy_board(board)
    opponent = WHITE if player == BLACK else BLACK

    def pro_legal(r, c):
        if opening != "pro":
            return True
        if move_num == 1 and (r, c) != (9, 9):
            return False
        if move_num == 3 and max(abs(r - 9), abs(c - 9)) < 3:
            return False
        return True

    candidates = [
        (r, c) for r, c in get_candidates(board_copy)
        if is_legal_move(board_copy, r, c, player)[0] and pro_legal(r, c)
    ]

    if not candidates:
        candidates = [
            (r, c) for r, c in get_candidates(board_copy)
            if is_legal_move(board_copy, r, c, player)[0]
        ]
    if not candidates:
        return get_candidates(board_copy)[0]

    # ── 1. Winning move ──
    for r, c in candidates:
        board_copy[r][c] = player
        if check_alignment(board_copy, r, c, player):
            board_copy[r][c] = 0
            return (r, c)
        board_copy[r][c] = 0

    # ── 2. Block opponent's winning move ──
    for r, c in candidates:
        board_copy[r][c] = opponent
        if check_alignment(board_copy, r, c, opponent):
            board_copy[r][c] = 0
            return (r, c)
        board_copy[r][c] = 0

    # ── 3. Block opponent 4-in-a-row ──
    for r, c in candidates:
        board_copy[r][c] = opponent
        for dr, dc in [(0,1),(1,0),(1,1),(1,-1)]:
            count = 1
            for step in [1, -1]:
                nr, nc = r + step*dr, c + step*dc
                while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board_copy[nr][nc] == opponent:
                    count += 1
                    nr += step*dr
                    nc += step*dc
            if count >= 4:
                board_copy[r][c] = 0
                return (r, c)
        board_copy[r][c] = 0

    # ── Minimax with iterative deepening ──
    best_move = candidates[0]
    start = time.perf_counter()

    for depth in range(1, max_depth + 1):
        if time.perf_counter() - start > TIME_LIMIT:
            break
        _, move = minimax(board_copy, depth, LOSE_SCORE, WIN_SCORE,
                         True, player, captures, start, TIME_LIMIT)
        if move and pro_legal(*move):
            best_move = move
        if time.perf_counter() - start > TIME_LIMIT:
            break

    return best_move

def order_moves(candidates, board, player, captures):
    scored = []
    for r, c in candidates:
        board[r][c] = player
        s = evaluate(board, player, captures)
        board[r][c] = 0
        scored.append((s, r, c))
    random.shuffle(scored)
    scored.sort(reverse=True, key=lambda x: x[0])
    return [(r, c) for s, r, c in scored[:8]]      # ← top 8