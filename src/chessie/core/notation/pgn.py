"""PGN parsing and serialization helpers."""

from __future__ import annotations

import re

from chessie.core.enums import GameResult
from chessie.core.notation.models import ParsedPgn, PgnMove

_PGN_HEADER_RE = re.compile(r'^\[(\w+)\s+"((?:[^"\\]|\\.)*)"\]\s*$')
_PGN_RESULT_TOKENS = {"1-0", "0-1", "1/2-1/2", "*"}
_MOVE_NUMBER_RE = re.compile(r"^\d+\.(?:\.\.)?$")


def pgn_result_token(result: GameResult) -> str:
    """Convert :class:`GameResult` to a PGN result token."""
    if result == GameResult.WHITE_WINS:
        return "1-0"
    if result == GameResult.BLACK_WINS:
        return "0-1"
    if result == GameResult.DRAW:
        return "1/2-1/2"
    return "*"


def game_result_from_pgn(token: str) -> GameResult:
    """Convert PGN result token to :class:`GameResult`."""
    if token == "1-0":
        return GameResult.WHITE_WINS
    if token == "0-1":
        return GameResult.BLACK_WINS
    if token == "1/2-1/2":
        return GameResult.DRAW
    return GameResult.IN_PROGRESS


def pgn_movetext_from_sans(sans: list[str], result_token: str) -> str:
    """Build PGN movetext from SAN moves and a result token."""
    return pgn_movetext_from_moves([PgnMove(san=san) for san in sans], result_token)


def pgn_movetext_from_moves(moves: list[PgnMove], result_token: str) -> str:
    """Build PGN movetext from mainline moves with optional comments."""
    parts: list[str] = []
    for ply, move in enumerate(moves):
        if ply % 2 == 0:
            parts.append(f"{(ply // 2) + 1}.")
        parts.append(move.san)
        if move.comment:
            # PGN comments cannot contain a closing brace.
            safe_comment = move.comment.replace("}", "]")
            parts.append(f"{{{safe_comment}}}")
    parts.append(result_token)
    return " ".join(parts)


def build_pgn(
    headers: dict[str, str],
    sans: list[str],
    result_token: str,
    comments: list[str | None] | None = None,
) -> str:
    """Build a single-game PGN document."""
    if comments is not None and len(comments) != len(sans):
        raise ValueError("PGN comments length must match SAN move length")

    moves: list[PgnMove] = []
    for idx, san in enumerate(sans):
        comment = ""
        if comments is not None and comments[idx]:
            comment = comments[idx] or ""
        moves.append(PgnMove(san=san, comment=comment))

    lines: list[str] = []
    for key, value in headers.items():
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'[{key} "{escaped}"]')
    lines.append("")
    lines.append(pgn_movetext_from_moves(moves, result_token))
    lines.append("")
    return "\n".join(lines)


def _append_comment(move: PgnMove, comment: str) -> None:
    clean = " ".join(comment.split())
    if not clean:
        return
    if move.comment:
        move.comment = f"{move.comment} {clean}"
    else:
        move.comment = clean


def _parse_pgn_movetext_mainline(movetext: str) -> tuple[list[PgnMove], str]:
    """Parse movetext and return mainline moves/comments plus result token."""
    moves: list[PgnMove] = []
    result_token = "*"
    variation_depth = 0
    idx = 0
    total = len(movetext)

    while idx < total:
        ch = movetext[idx]

        if ch.isspace():
            idx += 1
            continue

        if ch == "{":
            end = movetext.find("}", idx + 1)
            if end < 0:
                comment = movetext[idx + 1 :]
                idx = total
            else:
                comment = movetext[idx + 1 : end]
                idx = end + 1
            if variation_depth == 0 and moves:
                _append_comment(moves[-1], comment)
            continue

        if ch == ";":
            end = movetext.find("\n", idx + 1)
            if end < 0:
                end = total
            comment = movetext[idx + 1 : end]
            if variation_depth == 0 and moves:
                _append_comment(moves[-1], comment)
            idx = end
            continue

        if ch == "(":
            variation_depth += 1
            idx += 1
            continue

        if ch == ")":
            variation_depth = max(0, variation_depth - 1)
            idx += 1
            continue

        token_end = idx
        while (
            token_end < total
            and not movetext[token_end].isspace()
            and movetext[token_end] not in "{}();()"
        ):
            token_end += 1
        token = movetext[idx:token_end]
        idx = token_end

        if not token or variation_depth > 0:
            continue

        if token in _PGN_RESULT_TOKENS:
            result_token = token
            continue

        if _MOVE_NUMBER_RE.match(token):
            continue

        if token.startswith("$") and token[1:].isdigit():
            continue

        if token.startswith("..."):
            token = token[3:]
        token = token.lstrip(".")
        if not token:
            continue

        moves.append(PgnMove(san=token))

    return moves, result_token


def parse_pgn_game(pgn_text: str) -> ParsedPgn:
    """Parse a single PGN game into structured headers/moves/result."""
    headers: dict[str, str] = {}
    move_lines: list[str] = []
    in_headers = True

    for raw_line in pgn_text.splitlines():
        line = raw_line.strip()
        if not line:
            if in_headers and not headers:
                continue
            in_headers = False
            continue

        if in_headers and line.startswith("["):
            match = _PGN_HEADER_RE.match(line)
            if match is None:
                raise ValueError(f"Invalid PGN header line: {line}")
            key, raw_value = match.groups()
            value = raw_value.replace('\\"', '"').replace("\\\\", "\\")
            headers[key] = value
            continue

        in_headers = False
        if line.startswith("%"):
            continue
        move_lines.append(line)

    moves, result_token = _parse_pgn_movetext_mainline("\n".join(move_lines))
    header_result = headers.get("Result")
    if result_token == "*" and header_result in _PGN_RESULT_TOKENS:
        result_token = header_result

    return ParsedPgn(headers=headers, moves=moves, result_token=result_token)


def parse_pgn(pgn_text: str) -> tuple[dict[str, str], list[str], str]:
    """Backward-compatible parser returning headers + SAN mainline + result."""
    parsed = parse_pgn_game(pgn_text)
    return parsed.headers, [move.san for move in parsed.moves], parsed.result_token
