import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xiangqi import Game


def test_finished_game_has_no_move_hints():
    game = Game()
    game.winner = "r"

    assert game.moves((0, 6)) == []
