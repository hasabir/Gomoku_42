BOARD_SIZE = 19
CELL_SIZE = 42
MARGIN = 40
WINDOW_SIZE = CELL_SIZE * (BOARD_SIZE - 1) + 2 * MARGIN

EMPTY = 0
PLAYER1 = 1
PLAYER2 = 2
BLACK = 1
WHITE = 2


# Colors
BG_COLOR        = (220, 179, 92)
LINE_COLOR      = (0, 0, 0)
P1_COLOR        = (20, 20, 20)
P2_COLOR        = (240, 240, 240)
HIGHLIGHT_COLOR = (255, 0, 0)

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
