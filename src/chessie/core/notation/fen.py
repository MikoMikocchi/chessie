"""FEN parsing and serialization."""

from __future__ import annotations

from chessie.core.board import Board
from chessie.core.enums import CastlingRights, Color
from chessie.core.piece import Piece
from chessie.core.position import Position
from chessie.core.types import Square, make_square, parse_square, rank_of, square_name

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def position_from_fen(fen: str) -> Position:
    """Parse a FEN string into a :class:`Position`."""
    parts = fen.split()
    if not (4 <= len(parts) <= 6):
        raise ValueError(f"Invalid FEN (need 4-6 fields): {fen!r}")

    placement, side_part, castling_part, ep_part = parts[:4]

    # 1. Piece placement
    ranks = placement.split("/")
    if len(ranks) != 8:
        raise ValueError(f"Invalid FEN board (must contain 8 ranks): {fen!r}")
    board = Board()
    for rank_idx, rank_text in enumerate(ranks):
        rank = 7 - rank_idx
        file = 0
        for ch in rank_text:
            if ch.isdigit():
                step = int(ch)
                if not (1 <= step <= 8):
                    raise ValueError(f"Invalid FEN digit {ch!r}: {fen!r}")
                file += step
            else:
                if file >= 8:
                    raise ValueError(f"Invalid FEN rank width: {fen!r}")
                board[make_square(file, rank)] = Piece.from_char(ch)
                file += 1
            if file > 8:
                raise ValueError(f"Invalid FEN rank width: {fen!r}")
        if file != 8:
            raise ValueError(f"Invalid FEN rank width: {fen!r}")

    # 2. Side to move
    if side_part == "w":
        side = Color.WHITE
    elif side_part == "b":
        side = Color.BLACK
    else:
        raise ValueError(f"Invalid FEN side-to-move field: {side_part!r}")

    # 3. Castling
    castling = CastlingRights.NONE
    if castling_part != "-":
        rights = {
            "K": CastlingRights.WHITE_KINGSIDE,
            "Q": CastlingRights.WHITE_QUEENSIDE,
            "k": CastlingRights.BLACK_KINGSIDE,
            "q": CastlingRights.BLACK_QUEENSIDE,
        }
        seen: set[str] = set()
        for ch in castling_part:
            right = rights.get(ch)
            if right is None:
                raise ValueError(f"Invalid FEN castling field: {castling_part!r}")
            if ch in seen:
                raise ValueError(f"Invalid FEN castling field: {castling_part!r}")
            seen.add(ch)
            castling |= right

    # 4. En passant
    ep: Square | None = None
    if ep_part != "-":
        ep = parse_square(ep_part)
        ep_rank = rank_of(ep)
        if ep_rank not in (2, 5):
            raise ValueError(f"Invalid FEN en-passant square: {ep_part!r}")
        expected_ep_rank = 5 if side == Color.WHITE else 2
        if ep_rank != expected_ep_rank:
            raise ValueError(
                f"Invalid FEN en-passant square for side-to-move: {ep_part!r}"
            )

    # 5–6. Clocks (optional)
    if len(parts) > 4:
        halfmove = int(parts[4])
        if halfmove < 0:
            raise ValueError(f"Invalid FEN halfmove clock: {parts[4]!r}")
    else:
        halfmove = 0

    if len(parts) > 5:
        fullmove = int(parts[5])
        if fullmove < 1:
            raise ValueError(f"Invalid FEN fullmove number: {parts[5]!r}")
    else:
        fullmove = 1

    return Position(board, side, castling, ep, halfmove, fullmove)


def position_to_fen(pos: Position) -> str:
    """Serialise a :class:`Position` to FEN."""
    # 1. Board
    rows: list[str] = []
    for rank in range(7, -1, -1):
        empty = 0
        row = ""
        for file in range(8):
            piece = pos.board[make_square(file, rank)]
            if piece is None:
                empty += 1
            else:
                if empty:
                    row += str(empty)
                    empty = 0
                row += str(piece)
        if empty:
            row += str(empty)
        rows.append(row)
    board_str = "/".join(rows)

    # 2. Side
    side_str = "w" if pos.side_to_move == Color.WHITE else "b"

    # 3. Castling
    castling_str = ""
    if pos.castling & CastlingRights.WHITE_KINGSIDE:
        castling_str += "K"
    if pos.castling & CastlingRights.WHITE_QUEENSIDE:
        castling_str += "Q"
    if pos.castling & CastlingRights.BLACK_KINGSIDE:
        castling_str += "k"
    if pos.castling & CastlingRights.BLACK_QUEENSIDE:
        castling_str += "q"
    if not castling_str:
        castling_str = "-"

    # 4. En passant
    ep_str = square_name(pos.en_passant) if pos.en_passant is not None else "-"

    return f"{board_str} {side_str} {castling_str} {ep_str} {pos.halfmove_clock} {pos.fullmove_number}"
