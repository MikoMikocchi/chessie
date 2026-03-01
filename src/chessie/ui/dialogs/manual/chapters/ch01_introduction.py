"""Chapter 1 – Introduction to Chess."""

from __future__ import annotations

from chessie.ui.dialogs.manual.chapters._base import fen_diagram, wrap_page
from chessie.ui.dialogs.manual.models import Chapter, ChapterProvider, Page


class IntroductionChapter(ChapterProvider):
    """Overview of chess: history, goal, the board."""

    @property
    def chapter_id(self) -> str:
        return "ch01_intro"

    @property
    def order(self) -> int:
        return 10

    def build(self, lang: str) -> Chapter:
        if lang == "Russian":
            return self._build_ru()
        return self._build_en()

    # ── English ──────────────────────────────────────────────────────

    def _build_en(self) -> Chapter:
        pages = (
            Page(
                anchor="what_is_chess",
                html=wrap_page(
                    "<h1>What Is Chess?</h1>"
                    "<p>Chess is a two-player strategy board game played on a "
                    "64-square board arranged in an 8×8 grid. It is one of the "
                    "world's oldest and most popular games, with origins dating "
                    "back to 6th-century India.</p>"
                    "<p>Each player starts with <b>16 pieces</b>: one king, one "
                    "queen, two rooks, two bishops, two knights, and eight pawns.</p>"
                    '<div class="highlight-box">'
                    "<b>Objective:</b> Checkmate the opponent's king — place it "
                    "under an inescapable threat of capture."
                    "</div>"
                    "<p>A game can also end by resignation, draw agreement, "
                    "stalemate, or various draw rules (50-move, threefold "
                    "repetition, insufficient material).</p>",
                    anchor="what_is_chess",
                ),
            ),
            Page(
                anchor="the_board",
                html=wrap_page(
                    "<h1>The Chessboard</h1>"
                    "<p>The board has 64 squares — alternating light and dark — "
                    "arranged in 8 <b>ranks</b> (rows, numbered 1–8) and 8 "
                    "<b>files</b> (columns, lettered a–h).</p>"
                    "<p>When setting up the board, a <em>light square</em> must "
                    "be in each player's near-right corner.</p>"
                    + fen_diagram(
                        "8/8/8/8/8/8/8/8",
                        "The empty chessboard",
                    )
                    + "<p>Squares are named by combining the file letter and rank "
                    "number. For example, <b>e4</b> is the square on file e, "
                    "rank 4 — the centre of the board.</p>"
                    '<div class="note">Diagonals connect squares of the same '
                    "colour. Bishops always stay on their starting colour.</div>",
                    anchor="the_board",
                ),
            ),
            Page(
                anchor="starting_position",
                html=wrap_page(
                    "<h1>The Starting Position</h1>"
                    "<p>At the beginning of the game, pieces are placed as "
                    "shown below:</p>"
                    + fen_diagram(
                        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR",
                        "Starting position",
                    )
                    + "<p>White's pieces occupy ranks 1–2, Black's occupy ranks "
                    "7–8.</p>"
                    "<ul>"
                    "<li>Rooks stand in the corners (a1, h1 / a8, h8).</li>"
                    "<li>Knights stand next to rooks.</li>"
                    "<li>Bishops stand next to knights.</li>"
                    "<li>The <b>queen</b> goes on the square matching her colour "
                    "(white queen on a light square d1, black queen on d8).</li>"
                    "<li>The <b>king</b> occupies the remaining central square.</li>"
                    "<li>Pawns fill the entire second rank for each side.</li>"
                    "</ul>"
                    '<div class="note">Remember: "queen on her colour" — the '
                    "white queen starts on d1 (light), the black queen on d8 "
                    "(dark).</div>",
                    anchor="starting_position",
                ),
            ),
        )
        return Chapter(chapter_id=self.chapter_id, title="Introduction", pages=pages)

    # ── Russian ──────────────────────────────────────────────────────

    def _build_ru(self) -> Chapter:
        pages = (
            Page(
                anchor="what_is_chess",
                html=wrap_page(
                    "<h1>Что такое шахматы?</h1>"
                    "<p>Шахматы — стратегическая настольная игра для двух "
                    "игроков на доске из 64 клеток (8×8). Это одна из "
                    "старейших и популярнейших игр в мире, берущая начало "
                    "в Индии VI века.</p>"
                    "<p>У каждого игрока <b>16 фигур</b>: король, ферзь, "
                    "две ладьи, два слона, два коня и восемь пешек.</p>"
                    '<div class="highlight-box">'
                    "<b>Цель:</b> поставить мат королю соперника — создать "
                    "неотразимую угрозу его взятия."
                    "</div>"
                    "<p>Партия также может закончиться сдачей, соглашением "
                    "на ничью, патом или по правилам ничьей (правило 50 ходов, "
                    "троекратное повторение, недостаточный материал).</p>",
                    anchor="what_is_chess",
                ),
            ),
            Page(
                anchor="the_board",
                html=wrap_page(
                    "<h1>Шахматная доска</h1>"
                    "<p>Доска состоит из 64 клеток — попеременно светлых и "
                    "тёмных — расположенных в 8 <b>горизонталях</b> (ряды, "
                    "1–8) и 8 <b>вертикалях</b> (столбцы, a–h).</p>"
                    "<p>При расстановке доски <em>светлая клетка</em> должна "
                    "находиться в правом ближнем углу каждого игрока.</p>"
                    + fen_diagram(
                        "8/8/8/8/8/8/8/8",
                        "Пустая шахматная доска",
                    )
                    + "<p>Клетки именуются буквой вертикали и номером "
                    "горизонтали. Например, <b>e4</b> — клетка на "
                    "вертикали e, горизонтали 4.</p>"
                    '<div class="note">Диагонали соединяют клетки одного '
                    "цвета. Слоны всегда остаются на цвете, на котором "
                    "начали партию.</div>",
                    anchor="the_board",
                ),
            ),
            Page(
                anchor="starting_position",
                html=wrap_page(
                    "<h1>Начальная позиция</h1>"
                    "<p>В начале партии фигуры расставляются так:</p>"
                    + fen_diagram(
                        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR",
                        "Начальная позиция",
                    )
                    + "<p>Фигуры белых занимают горизонтали 1–2, чёрных — "
                    "7–8.</p>"
                    "<ul>"
                    "<li>Ладьи стоят по углам (a1, h1 / a8, h8).</li>"
                    "<li>Кони — рядом с ладьями.</li>"
                    "<li>Слоны — рядом с конями.</li>"
                    "<li><b>Ферзь</b> ставится на клетку своего цвета "
                    "(белый ферзь на d1 — светлая, чёрный на d8 — тёмная).</li>"
                    "<li><b>Король</b> занимает оставшуюся центральную клетку.</li>"
                    "<li>Пешки заполняют всю вторую горизонталь каждой стороны.</li>"
                    "</ul>"
                    '<div class="note">Запомните: «ферзь любит свой цвет» — '
                    "белый ферзь стоит на светлой d1, чёрный — на тёмной d8."
                    "</div>",
                    anchor="starting_position",
                ),
            ),
        )
        return Chapter(chapter_id=self.chapter_id, title="Введение", pages=pages)
