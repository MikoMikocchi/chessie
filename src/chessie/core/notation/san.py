"""SAN (Standard Algebraic Notation) conversion and parsing."""

from __future__ import annotations

from chessie.core.enums import MoveFlag, PieceType
from chessie.core.move import Move
from chessie.core.move_generator import MoveGenerator
from chessie.core.position import Position
from chessie.core.types import file_of, parse_square, rank_of, square_name

_SAN_PIECE: dict[PieceType, str] = {
    PieceType.KNIGHT: "N",
    PieceType.BISHOP: "B",
    PieceType.ROOK: "R",
    PieceType.QUEEN: "Q",
    PieceType.KING: "K",
}
_SAN_PIECE_REV: dict[str, PieceType] = {v: k for k, v in _SAN_PIECE.items()}


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
        is_capture = board[move.to_sq] is not None or move.flag == MoveFlag.EN_PASSANT

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
