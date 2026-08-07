from board import *
from constant import *
from board_to_px import board_to_px, px_to_board
import pygame
import sys
import time
import random
import math
from draw import Draw
from ai import get_move
from game_state import GameState




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

    place_stone(state, row, col)
    state.waiting_for_ai = False

def run_suggestion(state):
    #! suggestion logic to be iplimented 
    pass


# ─────────────────────────────────────────────────────────────────────────────
# FULL REDRAW
# ─────────────────────────────────────────────────────────────────────────────

def redraw(surface, fonts, state):
    """Composite the entire frame: board + stones + panel."""
    game = Draw(surface, fonts, state)
    game.draw_board()
    game.draw_all_stones(state.board,
                    last_move=state.last_move,
                    suggestion=state.suggestion if state.mode == MODE_HvH else None)
    game.draw_panel()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def mode_selection(surface, fonts, clock):
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
        
        Draw.draw_mode_screen(surface, fonts)
        pygame.display.flip()
        clock.tick(FPS)
    return mode




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
    mode = mode_selection(surface, fonts, clock)

    # ── Game initialisation ──
    state = GameState(mode)

    # ── If AI vs AI, start playing immediately ──          
    if state.mode == MODE_AIvAI:                            
        redraw(surface, fonts, state)                       
        pygame.display.flip()                               
        run_ai_turn(state, surface, fonts, clock)           
        pygame.time.wait(300)                               

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
                    mode = mode_selection(surface, fonts, clock)
                    state = GameState(mode)


            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state.game_over or state.mode == MODE_AIvAI or \
                (state.mode == MODE_HvAI and state.current_player == state.ai_player):
                    continue


                pos = px_to_board(*event.pos)
                if pos is None:
                    state.set_status("Click closer to an intersection.", error=True)
                    continue


                row, col = pos


                if state.place_stone(row, col) and not state.game_over:
                    # HvAI: trigger AI response
                    if state.mode == MODE_HvAI and state.current_player == state.ai_player:
                        redraw(surface, fonts, state)
                        pygame.display.flip()
                        print(state.waiting_for_ai)
                        run_ai_turn(state, surface, fonts, clock)
                        print(state.waiting_for_ai)

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
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)

