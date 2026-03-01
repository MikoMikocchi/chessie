"""Legal and pseudo-legal move generation + attack detection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from chessie.core.enums import CastlingRights, Color, MoveFlag, PieceType
from chessie.core.move import Move
from chessie.core.types import Square, make_square

if TYPE_CHECKING:
    from chessie.core.position import Position


KNIGHT_OFFSETS: tuple[tuple[int, int], ...] = (
    (-2, -1),
    (-2, 1),
    (-1, -2),
    (-1, 2),
    (1, -2),
    (1, 2),
    (2, -1),
    (2, 1),
)

KING_OFFSETS: tuple[tuple[int, int], ...] = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)

BISHOP_DIRS: tuple[tuple[int, int], ...] = ((-1, -1), (-1, 1), (1, -1), (1, 1))
ROOK_DIRS: tuple[tuple[int, int], ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))
QUEEN_DIRS: tuple[tuple[int, int], ...] = BISHOP_DIRS + ROOK_DIRS

_PROMOTION_TYPES: tuple[PieceType, ...] = (
    PieceType.QUEEN,
    PieceType.ROOK,
    PieceType.BISHOP,
    PieceType.KNIGHT,
)
_COLOR_OPPOSITE: tuple[Color, Color] = (Color.BLACK, Color.WHITE)


# -- Precomputed lookup tables ---------------------------------------------


def _build_targets(
    offsets: tuple[tuple[int, int], ...],
) -> tuple[tuple[Square, ...], ...]:
    targets: list[tuple[Square, ...]] = []
    for sq in range(64):
        file_idx = sq & 7
        rank_idx = sq >> 3
        moves: list[Square] = []
        for df, dr in offsets:
            af = file_idx + df
            ar = rank_idx + dr
            if 0 <= af < 8 and 0 <= ar < 8:
                moves.append(make_square(af, ar))
        targets.append(tuple(moves))
    return tuple(targets)


def _build_attack_masks(targets: tuple[tuple[Square, ...], ...]) -> tuple[int, ...]:
    masks: list[int] = [0] * 64
    for sq in range(64):
        mask = 0
        for to_sq in targets[sq]:
            mask |= 1 << to_sq
        masks[sq] = mask
    return tuple(masks)


def _build_pawn_attacker_masks() -> tuple[tuple[int, ...], tuple[int, ...]]:
    white_masks: list[int] = [0] * 64
    black_masks: list[int] = [0] * 64

    for sq in range(64):
        file_idx = sq & 7
        rank_idx = sq >> 3

        white_mask = 0
        if rank_idx > 0:
            if file_idx > 0:
                white_mask |= 1 << make_square(file_idx - 1, rank_idx - 1)
            if file_idx < 7:
                white_mask |= 1 << make_square(file_idx + 1, rank_idx - 1)

        black_mask = 0
        if rank_idx < 7:
            if file_idx > 0:
                black_mask |= 1 << make_square(file_idx - 1, rank_idx + 1)
            if file_idx < 7:
                black_mask |= 1 << make_square(file_idx + 1, rank_idx + 1)

        white_masks[sq] = white_mask
        black_masks[sq] = black_mask

    return (tuple(white_masks), tuple(black_masks))


def _build_rays(
    directions: tuple[tuple[int, int], ...],
) -> tuple[tuple[tuple[Square, ...], ...], ...]:
    rays_per_square: list[tuple[tuple[Square, ...], ...]] = []
    for sq in range(64):
        file_idx = sq & 7
        rank_idx = sq >> 3
        square_rays: list[tuple[Square, ...]] = []
        for df, dr in directions:
            af = file_idx + df
            ar = rank_idx + dr
            ray: list[Square] = []
            while 0 <= af < 8 and 0 <= ar < 8:
                ray.append(make_square(af, ar))
                af += df
                ar += dr
            square_rays.append(tuple(ray))
        rays_per_square.append(tuple(square_rays))
    return tuple(rays_per_square)


_KNIGHT_TARGETS = _build_targets(KNIGHT_OFFSETS)
_KING_TARGETS = _build_targets(KING_OFFSETS)
_KNIGHT_ATTACK_MASKS = _build_attack_masks(_KNIGHT_TARGETS)
_KING_ATTACK_MASKS = _build_attack_masks(_KING_TARGETS)
_PAWN_ATTACKER_MASKS = _build_pawn_attacker_masks()

_BISHOP_RAYS = _build_rays(BISHOP_DIRS)
_ROOK_RAYS = _build_rays(ROOK_DIRS)
_QUEEN_RAYS = _build_rays(QUEEN_DIRS)


class MoveGenerator:
    """Generates legal moves for a given :class:`Position`.

    The generator mutates the position via ``make_move`` / ``unmake_move``
    internally but always restores it before returning.
    """

    __slots__ = ("_pos", "_board")

    def __init__(self, position: Position) -> None:
        self._pos = position
        self._board = position.board

    # -- Public API ---------------------------------------------------------

    def generate_legal_moves(self) -> list[Move]:
        """All strictly legal moves for the side to move."""
        legal: list[Move] = []
        moving_color = self._pos.side_to_move
        append_legal = legal.append

        for move in self.generate_pseudo_legal_moves():
            self._pos.make_move(move)
            if not self.is_in_check(moving_color):
                append_legal(move)
            self._pos.unmake_move(move)
        return legal

    def generate_pseudo_legal_moves(self) -> list[Move]:
        """All pseudo-legal moves (may leave own king in check)."""
        moves: list[Move] = []
        color = self._pos.side_to_move
        board = self._board

        pawns = board.pieces_bitboard(color, PieceType.PAWN)
        while pawns:
            lsb = pawns & -pawns
            self._gen_pawn(lsb.bit_length() - 1, color, moves)
            pawns ^= lsb

        knights = board.pieces_bitboard(color, PieceType.KNIGHT)
        while knights:
            lsb = knights & -knights
            self._gen_knight(lsb.bit_length() - 1, color, moves)
            knights ^= lsb

        bishops = board.pieces_bitboard(color, PieceType.BISHOP)
        while bishops:
            lsb = bishops & -bishops
            sq = lsb.bit_length() - 1
            self._gen_sliding(sq, color, _BISHOP_RAYS[sq], moves)
            bishops ^= lsb

        rooks = board.pieces_bitboard(color, PieceType.ROOK)
        while rooks:
            lsb = rooks & -rooks
            sq = lsb.bit_length() - 1
            self._gen_sliding(sq, color, _ROOK_RAYS[sq], moves)
            rooks ^= lsb

        queens = board.pieces_bitboard(color, PieceType.QUEEN)
        while queens:
            lsb = queens & -queens
            sq = lsb.bit_length() - 1
            self._gen_sliding(sq, color, _QUEEN_RAYS[sq], moves)
            queens ^= lsb

        kings = board.pieces_bitboard(color, PieceType.KING)
        while kings:
            lsb = kings & -kings
            self._gen_king(lsb.bit_length() - 1, color, moves)
            kings ^= lsb

        return moves

    # -- Attack detection (public) -----------------------------------------

    def is_in_check(self, color: Color) -> bool:
        """Is *color*'s king attacked by the opponent?"""
        king_sq = self._board.king_square(color)
        return self.is_square_attacked(king_sq, _COLOR_OPPOSITE[int(color)])

    def is_square_attacked(self, sq: Square, by_color: Color) -> bool:
        """Is *sq* attacked by any piece of *by_color*?"""
        board = self._board
        by_idx = int(by_color)

        if (
            board.pieces_bitboard(by_color, PieceType.PAWN)
            & _PAWN_ATTACKER_MASKS[by_idx][sq]
        ):
            return True

        if board.pieces_bitboard(by_color, PieceType.KNIGHT) & _KNIGHT_ATTACK_MASKS[sq]:
            return True

        if board.pieces_bitboard(by_color, PieceType.KING) & _KING_ATTACK_MASKS[sq]:
            return True

        if board.pieces_bitboard(by_color, PieceType.BISHOP) or board.pieces_bitboard(
            by_color, PieceType.QUEEN
        ):
            for ray in _BISHOP_RAYS[sq]:
                for to_sq in ray:
                    piece = board[to_sq]
                    if piece is None:
                        continue
                    if piece.color == by_color and piece.piece_type in (
                        PieceType.BISHOP,
                        PieceType.QUEEN,
                    ):
                        return True
                    break

        if board.pieces_bitboard(by_color, PieceType.ROOK) or board.pieces_bitboard(
            by_color, PieceType.QUEEN
        ):
            for ray in _ROOK_RAYS[sq]:
                for to_sq in ray:
                    piece = board[to_sq]
                    if piece is None:
                        continue
                    if piece.color == by_color and piece.piece_type in (
                        PieceType.ROOK,
                        PieceType.QUEEN,
                    ):
                        return True
                    break

        return False

    # -- Piece-specific generators (private) -------------------------------

    def _gen_pawn(self, sq: Square, color: Color, moves: list[Move]) -> None:
        board = self._board
        file_idx = sq & 7
        rank_idx = sq >> 3

        if color == Color.WHITE:
            one_step = sq + 8
            if one_step < 64 and board.is_empty(one_step):
                if rank_idx == 6:
                    for pt in _PROMOTION_TYPES:
                        moves.append(Move(sq, one_step, MoveFlag.PROMOTION, pt))
                else:
                    moves.append(Move(sq, one_step))
                    if rank_idx == 1:
                        two_step = sq + 16
                        if board.is_empty(two_step):
                            moves.append(Move(sq, two_step, MoveFlag.DOUBLE_PAWN))

            cap_rank_valid = rank_idx < 7
            if cap_rank_valid and file_idx > 0:
                cap_sq = sq + 7
                target = board[cap_sq]
                if target is not None and target.color != color:
                    if rank_idx == 6:
                        for pt in _PROMOTION_TYPES:
                            moves.append(Move(sq, cap_sq, MoveFlag.PROMOTION, pt))
                    else:
                        moves.append(Move(sq, cap_sq))
                elif cap_sq == self._pos.en_passant:
                    moves.append(Move(sq, cap_sq, MoveFlag.EN_PASSANT))

            if cap_rank_valid and file_idx < 7:
                cap_sq = sq + 9
                target = board[cap_sq]
                if target is not None and target.color != color:
                    if rank_idx == 6:
                        for pt in _PROMOTION_TYPES:
                            moves.append(Move(sq, cap_sq, MoveFlag.PROMOTION, pt))
                    else:
                        moves.append(Move(sq, cap_sq))
                elif cap_sq == self._pos.en_passant:
                    moves.append(Move(sq, cap_sq, MoveFlag.EN_PASSANT))
            return

        # Black pawns
        one_step = sq - 8
        if one_step >= 0 and board.is_empty(one_step):
            if rank_idx == 1:
                for pt in _PROMOTION_TYPES:
                    moves.append(Move(sq, one_step, MoveFlag.PROMOTION, pt))
            else:
                moves.append(Move(sq, one_step))
                if rank_idx == 6:
                    two_step = sq - 16
                    if board.is_empty(two_step):
                        moves.append(Move(sq, two_step, MoveFlag.DOUBLE_PAWN))

        cap_rank_valid = rank_idx > 0
        if cap_rank_valid and file_idx > 0:
            cap_sq = sq - 9
            target = board[cap_sq]
            if target is not None and target.color != color:
                if rank_idx == 1:
                    for pt in _PROMOTION_TYPES:
                        moves.append(Move(sq, cap_sq, MoveFlag.PROMOTION, pt))
                else:
                    moves.append(Move(sq, cap_sq))
            elif cap_sq == self._pos.en_passant:
                moves.append(Move(sq, cap_sq, MoveFlag.EN_PASSANT))

        if cap_rank_valid and file_idx < 7:
            cap_sq = sq - 7
            target = board[cap_sq]
            if target is not None and target.color != color:
                if rank_idx == 1:
                    for pt in _PROMOTION_TYPES:
                        moves.append(Move(sq, cap_sq, MoveFlag.PROMOTION, pt))
                else:
                    moves.append(Move(sq, cap_sq))
            elif cap_sq == self._pos.en_passant:
                moves.append(Move(sq, cap_sq, MoveFlag.EN_PASSANT))

    def _gen_knight(self, sq: Square, color: Color, moves: list[Move]) -> None:
        board = self._board
        for to_sq in _KNIGHT_TARGETS[sq]:
            target = board[to_sq]
            if target is None or target.color != color:
                moves.append(Move(sq, to_sq))

    def _gen_sliding(
        self,
        sq: Square,
        color: Color,
        rays: tuple[tuple[Square, ...], ...],
        moves: list[Move],
    ) -> None:
        board = self._board
        for ray in rays:
            for to_sq in ray:
                target = board[to_sq]
                if target is None:
                    moves.append(Move(sq, to_sq))
                    continue
                if target.color != color:
                    moves.append(Move(sq, to_sq))
                break

    def _gen_king(self, sq: Square, color: Color, moves: list[Move]) -> None:
        board = self._board
        for to_sq in _KING_TARGETS[sq]:
            target = board[to_sq]
            if target is None or target.color != color:
                moves.append(Move(sq, to_sq))

        self._gen_castling(sq, color, moves)

    def _gen_castling(self, king_sq: Square, color: Color, moves: list[Move]) -> None:
        if self.is_in_check(color):
            return

        board = self._board
        opponent = _COLOR_OPPOSITE[int(color)]
        offset = 0 if color == Color.WHITE else 56

        ks = (
            CastlingRights.WHITE_KINGSIDE
            if color == Color.WHITE
            else CastlingRights.BLACK_KINGSIDE
        )
        if self._pos.castling & ks:
            f_sq = offset + 5
            g_sq = offset + 6
            if (
                board.is_empty(f_sq)
                and board.is_empty(g_sq)
                and not self.is_square_attacked(f_sq, opponent)
                and not self.is_square_attacked(g_sq, opponent)
            ):
                moves.append(Move(king_sq, g_sq, MoveFlag.CASTLE_KINGSIDE))

        qs = (
            CastlingRights.WHITE_QUEENSIDE
            if color == Color.WHITE
            else CastlingRights.BLACK_QUEENSIDE
        )
        if self._pos.castling & qs:
            b_sq = offset + 1
            c_sq = offset + 2
            d_sq = offset + 3
            if (
                board.is_empty(b_sq)
                and board.is_empty(c_sq)
                and board.is_empty(d_sq)
                and not self.is_square_attacked(c_sq, opponent)
                and not self.is_square_attacked(d_sq, opponent)
            ):
                moves.append(Move(king_sq, c_sq, MoveFlag.CASTLE_QUEENSIDE))
