"""Two-player Xiangqi: legal movement, self-check, checkmate and undo."""
from copy import deepcopy

NAMES = {"rK": "帅", "rA": "仕", "rE": "相", "rH": "马", "rR": "车", "rC": "炮", "rP": "兵",
         "bK": "将", "bA": "士", "bE": "象", "bH": "馬", "bR": "車", "bC": "砲", "bP": "卒"}


class Game:
    def __init__(self):
        self.board = [[None] * 9 for _ in range(10)]
        for color, back, cannon, pawn in [("b", 0, 2, 3), ("r", 9, 7, 6)]:
            for x, kind in enumerate("RHEAKAEHR"):
                self.board[back][x] = color + kind
            for x in (1, 7):
                self.board[cannon][x] = color + "C"
            for x in (0, 2, 4, 6, 8):
                self.board[pawn][x] = color + "P"
        self.turn = "r"
        self.history = []
        self.winner = None

    def king(self, side):
        return next(((x, y) for y in range(10) for x in range(9)
                     if self.board[y][x] == side + "K"), None)

    def pseudo(self, start, end):
        x, y = start
        a, b = end
        if not all(type(v) is int for v in (x, y, a, b)):
            return False
        if not (0 <= x < 9 and 0 <= a < 9 and 0 <= y < 10 and 0 <= b < 10):
            return False
        piece, target = self.board[y][x], self.board[b][a]
        if not piece or start == end or (target and target[0] == piece[0]):
            return False
        side, kind = piece
        dx, dy = a - x, b - y
        palace = 3 <= a <= 5 and (7 <= b <= 9 if side == "r" else 0 <= b <= 2)
        if kind == "H":
            if (abs(dx), abs(dy)) not in ((1, 2), (2, 1)):
                return False
            leg = (x + dx // 2, y) if abs(dx) == 2 else (x, y + dy // 2)
            return not self.board[leg[1]][leg[0]]
        if kind == "E":
            return (abs(dx) == abs(dy) == 2 and
                    (b >= 5 if side == "r" else b <= 4) and
                    not self.board[y + dy // 2][x + dx // 2])
        if kind == "A":
            return palace and abs(dx) == abs(dy) == 1
        if kind == "P":
            forward = -1 if side == "r" else 1
            crossed = y <= 4 if side == "r" else y >= 5
            return (dx == 0 and dy == forward) or (crossed and abs(dx) == 1 and dy == 0)
        if kind == "K" and abs(dx) + abs(dy) == 1:
            return palace
        if dx != 0 and dy != 0:
            return False
        if dx:
            blockers = sum(self.board[y][i] is not None for i in range(min(x, a) + 1, max(x, a)))
        else:
            blockers = sum(self.board[i][x] is not None for i in range(min(y, b) + 1, max(y, b)))
        if kind == "R":
            return blockers == 0
        if kind == "C":
            return blockers == (1 if target else 0)
        return kind == "K" and dx == 0 and target == ("bK" if side == "r" else "rK") and blockers == 0

    def checked(self, side):
        king = self.king(side)
        if king is None:
            return True
        return any(self.board[y][x] and self.board[y][x][0] != side and self.pseudo((x, y), king)
                   for y in range(10) for x in range(9))

    def legal(self, start, end, side=None):
        side = side or self.turn
        if not self.pseudo(start, end):
            return False
        x, y = start
        a, b = end
        if self.board[y][x][0] != side:
            return False
        piece, target = self.board[y][x], self.board[b][a]
        self.board[b][a], self.board[y][x] = piece, None
        safe = not self.checked(side)
        self.board[y][x], self.board[b][a] = piece, target
        return safe

    def moves(self, start):
        return [[a, b] for b in range(10) for a in range(9)
                if self.legal(start, (a, b))]

    def move(self, start, end):
        if self.winner or not self.legal(start, end):
            raise ValueError("这一步不符合象棋规则，或会让己方被将军。")
        self.history.append((deepcopy(self.board), self.turn, self.winner))
        x, y = start
        a, b = end
        self.board[b][a], self.board[y][x] = self.board[y][x], None
        mover = self.turn
        self.turn = "b" if self.turn == "r" else "r"
        if self.king(self.turn) is None or not any(
            self.board[y][x] and self.board[y][x][0] == self.turn and self.moves((x, y))
            for y in range(10) for x in range(9)
        ):
            self.winner = mover

    def undo(self):
        if not self.history:
            raise ValueError("还没有走棋，不能悔棋。")
        self.board, self.turn, self.winner = self.history.pop()

    def state(self):
        return {"board": self.board, "turn": self.turn, "winner": self.winner,
                "checked": self.checked(self.turn), "moves": len(self.history), "names": NAMES}
