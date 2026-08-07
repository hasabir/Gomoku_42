from board import *
from constant import *
from board_to_px import board_to_px, px_to_board
import pygame
import sys
import time
import random
import math
from draw import Draw

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
        if self._check_alignment_win(self.board, row, col, player):
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


    def _check_alignment_win(self, board, row, col, player):
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