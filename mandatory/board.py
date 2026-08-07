from constant import *

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

def copy_board(board):
    return [row[:] for row in board]

def is_valid_pos(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

def place_stone(state, row, col):
    """
    Attempt to place the current player's stone at (row, col).
    Returns True on success, False if the move was blocked.
    Handles captures, win detection, and turn switching.
    """
    player = state.current_player
    opponent = WHITE if player == BLACK else BLACK
    # ── Validate move ──
    if state.board[row][col] != 0:
        state.set_status("Cell already occupied.", error=True)
        return False

    if is_move_into_capture(state.board, row, col, player):
        state.set_status("You can't move into a capture.", error=True)
        return False
    # count = count_free_threes(state.board, row, col, player)

    if is_double_three(state.board, row, col, player): ####
        # check capture exception
        temp = [r[:] for r in state.board]
        temp[row][col] = player
        captured_temp = apply_captures(temp, row, col, player)
        if not captured_temp:
            state.set_status("Double-three is forbidden.", error=True)
            return False

    # ── Place the stone ──
    state.board[row][col] = player
    state.last_move = (row, col)
    state.status_msg = ""

    # ── Apply captures ── ####
    captured = apply_captures(state.board, row, col, player)
    if player == BLACK:
        state.cap_black += len(captured)
    else:
        state.cap_white += len(captured)

    # ── Win by capture ── #! logic not implimented yet
    if state.cap_black >= 10:
        state._win("Black wins by capture!\n(10 stones captured)")
        return True
    if state.cap_white >= 10:
        state._win("White wins by capture!\n(10 stones captured)")
        return True

    # ── Win by alignment (with endgame capture check) ──
    if check_alignment_win(state.board, row, col, player):
        alignment = get_alignment_stones(state.board, row, col, player)
        opp_caps  = state.cap_white if player == BLACK else state.cap_black
        if not can_capture_alignment(state.board, alignment, opponent):
            name = "Black" if player == BLACK else "White"
            state._win(f"{name} wins!\n5 in a row!")
            return True
        elif opp_caps >= 8:
            name = "Black" if opponent == BLACK else "White"
            state._win(f"{name} wins by capture!\n(broke the alignment)")
            return True
        # else game continues — alignment can be broken

    # ── Switch turn ──
    state.current_player = WHITE if player == BLACK else BLACK
    return True

def remove_stone(board, r, c):
    board[r][c] = EMPTY

# ─── CAPTURES ─────────────────────────────────────────────────────────────────

DIRECTIONS = [(0,1),(1,0),(1,1),(1,-1)]

def apply_captures(board, r, c, player):
    """After placing at (r,c), remove any captured opponent pairs. Returns captured positions."""
    opponent = PLAYER2 if player == PLAYER1 else PLAYER1
    captured = []
    all_dirs = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,-1),(1,-1),(-1,1)]
    for dr, dc in all_dirs:
        r1, c1 = r + dr, c + dc
        r2, c2 = r + 2*dr, c + 2*dc
        r3, c3 = r + 3*dr, c + 3*dc
        if (is_valid_pos(r3, c3)
                and board[r1][c1] == opponent
                and board[r2][c2] == opponent
                and board[r3][c3] == player):
            board[r1][c1] = EMPTY
            board[r2][c2] = EMPTY
            captured.append((r1, c1))
            captured.append((r2, c2))
    return captured

# ─── MOVE INTO CAPTURE CHECK ──────────────────────────────────────────────────

def is_move_into_capture(board, r, c, player):
    """Returns True if placing here would immediately get this stone captured."""
    opponent = PLAYER2 if player == PLAYER1 else PLAYER1
    all_dirs = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,-1),(1,-1),(-1,1)]
    for dr, dc in all_dirs:
        r1, c1 = r - dr, c - dc      # one step behind
        r2, c2 = r + dr, c + dc      # one step ahead
        r3, c3 = r + 2*dr, c + 2*dc  # two steps ahead
        # pattern: opponent . [r,c] . opponent  is NOT a capture of us
        # actual capture of us: opponent captures [r,c] means:
        # opponent at r1,c1 and at r3,c3 (flanking us + r2 which must be us too)
        # BUT we're a single stone so only pairs get captured — skip single
        # Real check: would placing here complete a pair that gets captured?
        # i.e. is there already our stone at r2,c2 flanked by opponent at r1,c1 and r3,c3?
        if (is_valid_pos(r1, c1) and is_valid_pos(r2, c2) and is_valid_pos(r3, c3)
                and board[r1][c1] == opponent
                and board[r2][c2] == player
                and board[r3][c3] == opponent):
            return True
    return False

# ─── FREE-THREE & DOUBLE-THREE ────────────────────────────────────────────────

def count_free_threes(board, r, c, player):
    """Count how many free-threes placing at (r,c) would create."""
    board[r][c] = player
    count = 0
    for dr, dc in DIRECTIONS:
        if _is_free_three_in_direction(board, r, c, player, dr, dc):
            count += 1
    board[r][c] = EMPTY
    return count



def _is_free_three_in_direction(board, r, c, player, dr, dc):
    cells = []
    for i in range(-4, 5):
        nr, nc = r + i*dr, c + i*dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            cells.append(board[nr][nc])
        else:
            cells.append(-1)  # wall
    # cells[4] is always (r,c)

    # 5-cell windows: . X X X .
    for start in range(0, 5):
        w = cells[start:start+5]
        if len(w) < 5:
            continue
        if not (start <= 4 <= start+4):
            continue
        if (w[0] == 0 and
            w[1] == player and
            w[2] == player and
            w[3] == player and
            w[4] == 0):
            return True

    # 6-cell windows for gapped patterns
    for start in range(0, 4):
        w = cells[start:start+6]
        if len(w) < 6:
            continue
        if not (start <= 4 <= start+5):
            continue
        # . X X . X .
        if (w[0] == 0 and w[1] == player and w[2] == player and
            w[3] == 0 and w[4] == player and w[5] == 0):
            return True
        # . X . X X .
        if (w[0] == 0 and w[1] == player and w[2] == 0 and
            w[3] == player and w[4] == player and w[5] == 0):
            return True

    return False

def is_double_three(board, r, c, player):
    """Returns True if placing at (r,c) creates 2+ free-threes (forbidden)."""
    return count_free_threes(board, r, c, player) >= 2

# ─── WIN DETECTION ────────────────────────────────────────────────────────────

def check_alignment(board, r, c, player):
    """Returns True if there's a 5+ alignment through (r,c) for player."""
    for dr, dc in DIRECTIONS:
        count = 1
        for step in [1, -1]:
            nr, nc = r + step*dr, c + step*dc
            while is_valid_pos(nr, nc) and board[nr][nc] == player:
                count += 1
                nr += step*dr
                nc += step*dc
        if count >= 5:
            return True
    return False

def get_alignment_stones(board, r, c, player):
    """Returns list of positions forming the 5+ alignment through (r,c)."""
    for dr, dc in DIRECTIONS:
        stones = [(r, c)]
        for step in [1, -1]:
            nr, nc = r + step*dr, c + step*dc
            while is_valid_pos(nr, nc) and board[nr][nc] == player:
                stones.append((nr, nc))
                nr += step*dr
                nc += step*dc
        if len(stones) >= 5:
            return stones
    return []

def can_capture_alignment(board, alignment, opponent):
    """
    Endgame capture check:
    Can opponent break the alignment by capturing a pair from it?
    Also checks if opponent is at 4 captures and can reach 5 (win by capture).
    """
    for r, c in alignment:
        # try all 8 directions: can opponent flank a pair containing (r,c)?
        all_dirs = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,-1),(1,-1),(-1,1)]
        for dr, dc in all_dirs:
            r1, c1 = r - dr, c - dc
            r2, c2 = r + dr, c + dc
            # pattern: if (r,c) and (r2,c2) are both player stones
            # and (r1,c1) and (r+2dr, c+2dc) are opponent → capture removes them
            r3, c3 = r + 2*dr, c + 2*dc
            if (is_valid_pos(r1,c1) and is_valid_pos(r2,c2) and is_valid_pos(r3,c3)
                    and board[r2][c2] == board[r][c]   # both same player
                    and board[r1][c1] == opponent
                    and board[r3][c3] == opponent):
                return True
    return False


def check_win(board, r, c, player, captures):
    """
    Full win check after placing at (r,c).
    captures = {PLAYER1: int, PLAYER2: int}
    Returns: 'alignment', 'capture', or None
    """
    opponent = PLAYER2 if player == PLAYER1 else PLAYER1

    # Win by capture
    if captures[player] >= 10:
        return 'capture'

    # Win by alignment — subject to endgame capture check
    if check_alignment(board, r, c, player):
        alignment = get_alignment_stones(board, r, c, player)
        if not can_capture_alignment(board, alignment, opponent, captures):
            return 'alignment'
        # If opponent can capture AND is at 4 pairs already → opponent wins
        if captures[opponent] >= 8:  # 8 = 4 pairs captured already
            return 'capture_opponent'

    return None

# ─── MOVE VALIDATION (main entry point) ───────────────────────────────────────

def is_legal_move(board, r, c, player, check_double_three=True):
    """
    Full move legality check. Returns (bool, reason).
    Your partner calls this too.
    """
    if not is_valid_pos(r, c):
        return False, "out of bounds"
    if board[r][c] != EMPTY:
        return False, "cell occupied"
    if is_move_into_capture(board, r, c, player):
        return False, "move into capture"
    if check_double_three:
        # Exception: double-three is allowed if it also causes a capture
        temp = copy_board(board)
        captured = apply_captures(temp, r, c, player)
        if not captured and is_double_three(board, r, c, player):
            return False, "double three"
    return True, "ok"







