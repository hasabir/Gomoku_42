from constant import *


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
    try:
        col = round((px - MARGIN) / CELL)
        row = round((py - MARGIN) / CELL)
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return None
        # Reject clicks that are more than half a cell away
        cx, cy = board_to_px(row, col)
        if abs(px - cx) <= CELL // 2 and abs(py - cy) <= CELL // 2:
            return row, col
        return None
    except Exception():

        pygame.quit()
        sys.exit()