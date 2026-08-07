import pygame
import sys
import time
import random
import math
from board_to_px import board_to_px, px_to_board

from constant import *



class Draw:
    def __init__(self, surface, fonts, state):
        self.surface = surface
        self.fonts = fonts
        self.state = state



    def draw_board(self):
        """Draw the wooden Goban: background, grid lines, and star points."""
        # Wood background with a subtle radial gradient effect via concentric rects
        self.surface.fill(C_WOOD_BG)
        for i in range(12):
            shade = max(0, 15 - i * 1)
            r = pygame.Rect(i*2, i*2, BOARD_PX - i*4, BOARD_PX - i*4)
            pygame.draw.rect(self.surface, (
                min(255, C_WOOD_LIGHT[0] - shade),
                min(255, C_WOOD_LIGHT[1] - shade),
                min(255, C_WOOD_LIGHT[2] - shade),
            ), r, 2)

        # Grid lines
        for i in range(BOARD_SIZE):
            x = MARGIN + i * CELL
            y = MARGIN + i * CELL
            pygame.draw.line(self.surface, C_WOOD_DARK, (MARGIN, y), (MARGIN + (BOARD_SIZE-1)*CELL, y), 1)
            pygame.draw.line(self.surface, C_WOOD_DARK, (x, MARGIN), (x, MARGIN + (BOARD_SIZE-1)*CELL), 1)

        # Border (thicker outer lines)
        pygame.draw.rect(self.surface, C_WOOD_DARK,
            (MARGIN, MARGIN, (BOARD_SIZE-1)*CELL, (BOARD_SIZE-1)*CELL), 2)



    def draw_all_stones(self, board, last_move=None, suggestion=None):
        """Redraw every stone on the board, plus last-move marker and suggestion."""
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] != 0:
                    self._draw_stone(self.surface, r, c, board[r][c])

        # Small red dot on the last placed stone
        if last_move:
            lr, lc = last_move
            cx, cy = board_to_px(lr, lc)
            pygame.draw.circle(self.surface, C_LAST_MOVE, (cx, cy), 4)

        # Yellow suggestion ring (hotseat mode)
        if suggestion:
            sr, sc = suggestion
            cx, cy = board_to_px(sr, sc)
            pygame.draw.circle(self.surface, C_SUGGEST, (cx, cy), CELL//2 - 3, 3)


    def draw_panel(self):
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
        pygame.draw.rect(self.surface, C_PANEL_BG, panel_rect)

        f_title  = self.fonts['title']
        f_body   = self.fonts['body']
        f_small  = self.fonts['small']
        f_big    = self.fonts['big']

        x = BOARD_PX + 20
        y = 28

        # ── Title ──
        title = self.surface.blit(f_title.render("GOMOKU", True, C_TEXT_HI), (x, y))
        y += title.height + 4
        # mode_name = "Human vs AI" if state.mode == MODE_HvAI else "Hotseat"
        if self.state.mode == MODE_HvAI:
            mode_name = "Human vs AI"
        elif self.state.mode == MODE_HvH:
            mode_name = "Hotseat"
        else:
            mode_name = "AI vs AI"
        self.surface.blit(f_small.render(mode_name, True, C_TEXT_LO), (x, y))
        y += 28

        # Divider
        pygame.draw.line(self.surface, C_PANEL_LINE,
                        (BOARD_PX + 12, y), (BOARD_PX + PANEL_W - 12, y), 1)
        y += 16

        # ── Turn indicator ──
        if not self.state.game_over:
            name  = "Black" if self.state.current_player == BLACK else "White"
            color = (50, 50, 50) if self.state.current_player == BLACK else (230, 230, 210)
            # Small stone icon
            pygame.draw.circle(self.surface, color, (x + 10, y + 10), 10)
            if self.state.current_player == WHITE:
                pygame.draw.circle(self.surface, (150, 140, 120), (x + 10, y + 10), 10, 1)
            label = f_body.render(f"  {name}'s turn", True, C_TEXT_WHITE)
            self.surface.blit(label, (x + 12, y + 2))
        y += 36

        # Divider
        pygame.draw.line(self.surface, C_PANEL_LINE,
                        (BOARD_PX + 12, y), (BOARD_PX + PANEL_W - 12, y), 1)
        y += 18

        # ── Capture counters ──
        self.surface.blit(f_small.render("CAPTURES", True, C_TEXT_LO), (x, y))
        y += 22

        # Black captures
        pygame.draw.circle(self.surface, C_BLACK_STONE, (x + 10, y + 10), 9)
        bc_txt = f_body.render(f"  Black:  {self.state.cap_black:2d} / 10", True, C_TEXT_WHITE)
        self.surface.blit(bc_txt, (x + 12, y + 1))
        y += 32

        # White captures
        pygame.draw.circle(self.surface, C_WHITE_STONE, (x + 10, y + 10), 9)
        pygame.draw.circle(self.surface, (150, 140, 120), (x + 10, y + 10), 9, 1)
        wc_txt = f_body.render(f"  White:  {self.state.cap_white:2d} / 10", True, C_TEXT_WHITE)
        self.surface.blit(wc_txt, (x + 12, y + 1))
        y += 38

        # Divider
        pygame.draw.line(self.surface, C_PANEL_LINE,
                        (BOARD_PX + 12, y), (BOARD_PX + PANEL_W - 12, y), 1)
        y += 18

        # ── AI Move Timer ──
        self.surface.blit(f_small.render("AI MOVE TIMER", True, C_TEXT_LO), (x, y))
        y += 22
        timer_ms = self.state.ai_move_time_ms
        if timer_ms is None:
            timer_str = "—"
            timer_color = C_TEXT_LO
        else:
            timer_str = f"{timer_ms:.1f} ms"
            timer_color = C_MSG_OK if timer_ms < 500 else C_MSG_ERR
        timer_surf = f_big.render(timer_str, True, timer_color)
        self.surface.blit(timer_surf, (x, y))
        y += timer_surf.get_height() + 6

        # Warning if over 500 ms
        if timer_ms and timer_ms >= 500:
            warn = f_small.render("⚠ AI too slow (>500 ms)", True, C_MSG_ERR)
            self.surface.blit(warn, (x, y))
            y += 20
        y += 10

        # Divider
        pygame.draw.line(self.surface, C_PANEL_LINE,
                        (BOARD_PX + 12, y), (BOARD_PX + PANEL_W - 12, y), 1)
        y += 18

        # ── Suggestion note (hotseat) ──
        if self.state.mode == MODE_HvH and self.state.suggestion:
            sr, sc = self.state.suggestion
            sg_txt = f_small.render(
                f"Suggestion: ({sr},{sc})", True, C_SUGGEST)
            self.surface.blit(sg_txt, (x, y))
            y += 22
            hint = f_small.render("(yellow ring on board)", True, C_TEXT_LO)
            self.surface.blit(hint, (x, y))
            y += 28

        # Divider
        pygame.draw.line(self.surface, C_PANEL_LINE,
                        (BOARD_PX + 12, y), (BOARD_PX + PANEL_W - 12, y), 1)
        y += 18

        # ── Status message ──
        if self.state.status_msg:
            msg_color = C_MSG_ERR if self.state.status_is_error else C_MSG_OK
            for line in self._wrap(self.state.status_msg, f_small, PANEL_W - 32):
                self.surface.blit(f_small.render(line, True, msg_color), (x, y))
                y += 20
        y += 10

        # ── Win overlay ──
        if self.state.game_over:
            self._draw_win_overlay(self.surface, self.fonts, self.state.win_message)

        # ── Key hints at bottom ──
        hints = [
            "R  –  restart",
            "Q  –  quit",
        ]
        hy = WIN_H - 14 - len(hints) * 18
        for hint in hints:
            self.surface.blit(f_small.render(hint, True, C_TEXT_LO), (x, hy))
            hy += 18


    def _draw_stone(self, surface, row, col, player, alpha=255):
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

    def _draw_win_overlay(self, surface, fonts, message):
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

    def _wrap(self, text, font, max_width):
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
    @staticmethod
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
