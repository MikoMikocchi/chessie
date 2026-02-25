"""FEN / SAN notation parsing and serialisation."""

from __future__ import annotations

from chessie.core.board import Board
from chessie.core.enums import CastlingRights, Color, MoveFlag, PieceType
from chessie.core.move import Move
from chessie.core.move_generator import MoveGenerator
from chessie.core.piece import Piece
from chessie.core.position import Position
from chessie.core.types import Square, file_of, make_square, parse_square, rank_of, square_name

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

_SAN_PIECE: dict[PieceType, str] = {
    PieceType.KNIGHT: "N",
    PieceType.BISHOP: "B",
    PieceType.ROOK: "R",
    PieceType.QUEEN: "Q",
    PieceType.KING: "K",
}
_SAN_PIECE_REV: dict[str, PieceType] = {v: k for k, v in _SAN_PIECE.items()}


# ── FEN ──────────────────────────────────────────────────────────────────────


def position_from_fen(fen: str) -> Position:
    """Parse a FEN string into a :class:`Position`."""
    parts = fen.split()
    if len(parts) < 4:
        raise ValueError(f"Invalid FEN (need ≥ 4 fields): {fen!r}")

    # 1. Piece placement
    board = Board()
    rank = 7
    file = 0
    for ch in parts[0]:
        if ch == "/":
            rank -= 1
            file = 0
        elif ch.isdigit():
            file += int(ch)
        else:
            board[make_square(file, rank)] = Piece.from_char(ch)
            file += 1

    # 2. Side to move
    side = Color.WHITE if parts[1] == "w" else Color.BLACK

    # 3. Castling
    castling = CastlingRights.NONE
    if parts[2] != "-":
        for ch in parts[2]:
            if ch == "K":
                castling |= CastlingRights.WHITE_KINGSIDE
            elif ch == "Q":
                castling |= CastlingRights.WHITE_QUEENSIDE
            elif ch == "k":
                castling |= CastlingRights.BLACK_KINGSIDE
            elif ch == "q":
                castling |= CastlingRights.BLACK_QUEENSIDE

    # 4. En passant
    ep: Square | None = None
    if parts[3] != "-":
        ep = parse_square(parts[3])

    # 5–6. Clocks (optional)
    halfmove = int(parts[4]) if len(parts) > 4 else 0
    fullmove = int(parts[5]) if len(parts) > 5 else 1

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


# ── SAN (Standard Algebraic Notation) ────────────────────────────────────────


def move_to_san(position: Position, move: Move) -> str:
    """Convert a legal *move* to SAN given the *position* before the move."""
    board = position.board
    piece = board[move.from_sq]
    assert piece is not None

    # Castling
    if move.flag == MoveFlag.CASTLE_KINGSIDE:
        san = "O-O"
    elif move.flag == MoveFlag.CASTLE_QUEENSIDE:
        san = "O-O-O"
    else:
        san = ""
        is_capture = (
            board[move.to_sq] is not None or move.flag == MoveFlag.EN_PASSANT
        )

        if piece.piece_type == PieceType.PAWN:
            if is_capture:
                san += chr(ord("a") + file_of(move.from_sq))
        else:
            san += _SAN_PIECE[piece.piece_type]

            # Disambiguation
            gen = MoveGenerator(position)
            legal = gen.generate_legal_moves()
            ambiguous = [
                m
                for m in legal
                if m.to_sq == move.to_sq
                and m.from_sq != move.from_sq
                and board[m.from_sq] is not None
                and board[m.from_sq].piece_type == piece.piece_type  # type: ignore[union-attr]
            ]
            if ambiguous:
                same_file = any(
                    file_of(m.from_sq) == file_of(move.from_sq) for m in ambiguous
                )
                same_rank = any(
                    rank_of(m.from_sq) == rank_of(move.from_sq) for m in ambiguous
                )
                if not same_file:
                    san += chr(ord("a") + file_of(move.from_sq))
                elif not same_rank:
                    san += str(rank_of(move.from_sq) + 1)
                else:
                    san += square_name(move.from_sq)

        if is_capture:
            san += "x"

        san += square_name(move.to_sq)

        if move.flag == MoveFlag.PROMOTION and move.promotion is not None:
            san += "=" + _SAN_PIECE[move.promotion]

    # Check / checkmate suffix
    position.make_move(move)
    gen_after = MoveGenerator(position)
    if gen_after.is_in_check(position.side_to_move):
        legal_after = gen_after.generate_legal_moves()
        san += "#" if not legal_after else "+"
    position.unmake_move(move)

    return san


def parse_san(position: Position, san: str) -> Move:
    """Parse a SAN string into a :class:`Move` given the current *position*."""
    gen = MoveGenerator(position)
    legal = gen.generate_legal_moves()

    clean = san.rstrip("+#!?")

    # Castling
    if clean in ("O-O", "0-0"):
        for m in legal:
            if m.flag == MoveFlag.CASTLE_KINGSIDE:
                return m
        raise ValueError(f"Illegal move: {san}")

    if clean in ("O-O-O", "0-0-0"):
        for m in legal:
            if m.flag == MoveFlag.CASTLE_QUEENSIDE:
                return m
        raise ValueError(f"Illegal move: {san}")

    # Promotion
    promotion: PieceType | None = None
    if "=" in clean:
        promotion = _SAN_PIECE_REV.get(clean[-1])
        clean = clean[:-2]  # drop "=Q" etc.

    # Destination (last two chars)
    to_sq = parse_square(clean[-2:])
    clean = clean[:-2]

    # Capture marker
    if clean.endswith("x"):
        clean = clean[:-1]

    # Piece type
    if clean and clean[0] in _SAN_PIECE_REV:
        piece_type = _SAN_PIECE_REV[clean[0]]
        clean = clean[1:]
    else:
        piece_type = PieceType.PAWN

    # Disambiguation
    from_file: int | None = None
    from_rank: int | None = None
    if len(clean) == 2:
        from_file = ord(clean[0]) - ord("a")
        from_rank = int(clean[1]) - 1
    elif len(clean) == 1:
        if clean[0].isalpha():
            from_file = ord(clean[0]) - ord("a")
        else:
            from_rank = int(clean[0]) - 1

    # Find matching legal move
    candidates: list[Move] = []
    for m in legal:
        p = position.board[m.from_sq]
        if p is None or p.piece_type != piece_type:
            continue
        if m.to_sq != to_sq:
            continue
        if promotion is not None and m.promotion != promotion:
            continue
        if from_file is not None and file_of(m.from_sq) != from_file:
            continue
        if from_rank is not None and rank_of(m.from_sq) != from_rank:
            continue
        candidates.append(m)

    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise ValueError(f"Illegal move: {san}")
    raise ValueError(f"Ambiguous move: {san} → {candidates}")
