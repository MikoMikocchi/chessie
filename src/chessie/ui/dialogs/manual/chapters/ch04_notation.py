"""Chapter 4 – Chess Notation."""

from __future__ import annotations

from chessie.ui.dialogs.manual.chapters._base import fen_diagram, wrap_page
from chessie.ui.dialogs.manual.models import Chapter, ChapterProvider, Page


class NotationChapter(ChapterProvider):
    """Algebraic notation, PGN basics."""

    @property
    def chapter_id(self) -> str:
        return "ch04_notation"

    @property
    def order(self) -> int:
        return 40

    def build(self, lang: str) -> Chapter:
        if lang == "Russian":
            return self._build_ru()
        return self._build_en()

    # ── English ──────────────────────────────────────────────────────

    def _build_en(self) -> Chapter:
        pages = (
            Page(
                anchor="algebraic",
                html=wrap_page(
                    "<h1>Algebraic Notation</h1>"
                    "<p>Chess moves are recorded using <b>algebraic notation"
                    "</b>. Each square has a unique name formed by its "
                    "<b>file letter</b> (a–h) and <b>rank number</b> (1–8).</p>"
                    + fen_diagram(
                        "8/8/8/8/4P3/8/8/8",
                        "The square e4",
                        "e4",
                    )
                    + "<h2>Recording Moves</h2>"
                    "<p>A move is written as the <b>piece letter</b> followed "
                    "by the <b>destination square</b>:</p>"
                    "<table>"
                    "<tr><th>Piece</th><th>Letter</th></tr>"
                    "<tr><td>King</td><td>K</td></tr>"
                    "<tr><td>Queen</td><td>Q</td></tr>"
                    "<tr><td>Rook</td><td>R</td></tr>"
                    "<tr><td>Bishop</td><td>B</td></tr>"
                    "<tr><td>Knight</td><td>N</td></tr>"
                    "<tr><td>Pawn</td><td>(none)</td></tr>"
                    "</table>"
                    "<p>Examples: <span class='move'>Nf3</span> = knight to f3, "
                    "<span class='move'>e4</span> = pawn to e4.</p>",
                    anchor="algebraic",
                ),
            ),
            Page(
                anchor="symbols",
                html=wrap_page(
                    "<h1>Special Symbols</h1>"
                    "<h2>Captures</h2>"
                    "<p>An <b>×</b> or <b>x</b> indicates a capture: "
                    "<span class='move'>Bxf7</span> = bishop captures on f7.</p>"
                    "<p>For pawn captures, the <b>file of departure</b> is "
                    "written: <span class='move'>exd5</span> = pawn on the "
                    "e-file captures on d5.</p>"
                    "<h2>Check and Checkmate</h2>"
                    "<ul>"
                    "<li><span class='move'>+</span> — check</li>"
                    "<li><span class='move'>#</span> — checkmate</li>"
                    "</ul>"
                    "<p>Example: <span class='move'>Qh7#</span> = queen to h7, "
                    "checkmate.</p>"
                    "<h2>Castling</h2>"
                    "<ul>"
                    "<li><span class='move'>O-O</span> — kingside castling</li>"
                    "<li><span class='move'>O-O-O</span> — queenside castling</li>"
                    "</ul>"
                    "<h2>Promotion</h2>"
                    "<p><span class='move'>e8=Q</span> — pawn promotes to a "
                    "queen on e8.</p>"
                    "<h2>Annotations</h2>"
                    "<table>"
                    "<tr><th>Symbol</th><th>Meaning</th></tr>"
                    "<tr><td>!</td><td>Good move</td></tr>"
                    "<tr><td>!!</td><td>Brilliant move</td></tr>"
                    "<tr><td>?</td><td>Mistake</td></tr>"
                    "<tr><td>??</td><td>Blunder</td></tr>"
                    "<tr><td>!?</td><td>Interesting move</td></tr>"
                    "<tr><td>?!</td><td>Dubious move</td></tr>"
                    "</table>",
                    anchor="symbols",
                ),
            ),
            Page(
                anchor="pgn",
                html=wrap_page(
                    "<h1>PGN Format</h1>"
                    "<p><b>PGN</b> (Portable Game Notation) is a standard text "
                    "format for recording chess games. Chessie can load and save "
                    "PGN files.</p>"
                    "<h2>Structure</h2>"
                    "<p>A PGN file has two parts:</p>"
                    "<ol>"
                    "<li><b>Tag pairs</b> (metadata in square brackets).</li>"
                    "<li><b>Move text</b> (moves in algebraic notation).</li>"
                    "</ol>"
                    '<div class="highlight-box">'
                    '<p style="font-family: monospace; font-size: 12px;">'
                    '[Event "Casual Game"]<br>'
                    '[Site "Internet"]<br>'
                    '[Date "2025.01.15"]<br>'
                    '[White "Alice"]<br>'
                    '[Black "Bob"]<br>'
                    '[Result "1-0"]<br><br>'
                    "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0"
                    "</p>"
                    "</div>"
                    "<h2>Result Codes</h2>"
                    "<ul>"
                    "<li><span class='move'>1-0</span> — White wins</li>"
                    "<li><span class='move'>0-1</span> — Black wins</li>"
                    "<li><span class='move'>1/2-1/2</span> — Draw</li>"
                    "<li><span class='move'>*</span> — Game in progress</li>"
                    "</ul>"
                    '<div class="note">Use <b>Ctrl+O</b> to open a PGN file '
                    "and <b>Ctrl+S</b> to save the current game.</div>",
                    anchor="pgn",
                ),
            ),
        )
        return Chapter(chapter_id=self.chapter_id, title="Notation", pages=pages)

    # ── Russian ──────────────────────────────────────────────────────

    def _build_ru(self) -> Chapter:
        pages = (
            Page(
                anchor="algebraic",
                html=wrap_page(
                    "<h1>Алгебраическая нотация</h1>"
                    "<p>Ходы записываются <b>алгебраической нотацией</b>. "
                    "Каждая клетка имеет уникальное имя из <b>буквы "
                    "вертикали</b> (a–h) и <b>номера горизонтали</b> (1–8).</p>"
                    + fen_diagram(
                        "8/8/8/8/4P3/8/8/8",
                        "Поле e4",
                        "e4",
                    )
                    + "<h2>Запись ходов</h2>"
                    "<p>Ход записывается как <b>буква фигуры</b> + <b>поле "
                    "назначения</b>:</p>"
                    "<table>"
                    "<tr><th>Фигура</th><th>Обозначение</th></tr>"
                    "<tr><td>Король</td><td>Кр (K)</td></tr>"
                    "<tr><td>Ферзь</td><td>Ф (Q)</td></tr>"
                    "<tr><td>Ладья</td><td>Л (R)</td></tr>"
                    "<tr><td>Слон</td><td>С (B)</td></tr>"
                    "<tr><td>Конь</td><td>К (N)</td></tr>"
                    "<tr><td>Пешка</td><td>(не указывается)</td></tr>"
                    "</table>"
                    "<p>Примеры: <span class='move'>Nf3</span> = конь на f3, "
                    "<span class='move'>e4</span> = пешка на e4.</p>",
                    anchor="algebraic",
                ),
            ),
            Page(
                anchor="symbols",
                html=wrap_page(
                    "<h1>Специальные обозначения</h1>"
                    "<h2>Взятия</h2>"
                    "<p>Символ <b>×</b> или <b>x</b> обозначает взятие: "
                    "<span class='move'>Bxf7</span> = слон бьёт на f7.</p>"
                    "<p>Для пешечных взятий указывается <b>вертикаль "
                    "отправления</b>: <span class='move'>exd5</span>.</p>"
                    "<h2>Шах и мат</h2>"
                    "<ul>"
                    "<li><span class='move'>+</span> — шах</li>"
                    "<li><span class='move'>#</span> — мат</li>"
                    "</ul>"
                    "<h2>Рокировка</h2>"
                    "<ul>"
                    "<li><span class='move'>O-O</span> — короткая</li>"
                    "<li><span class='move'>O-O-O</span> — длинная</li>"
                    "</ul>"
                    "<h2>Превращение</h2>"
                    "<p><span class='move'>e8=Q</span> — пешка превращается "
                    "в ферзя на e8.</p>"
                    "<h2>Оценочные символы</h2>"
                    "<table>"
                    "<tr><th>Символ</th><th>Значение</th></tr>"
                    "<tr><td>!</td><td>Хороший ход</td></tr>"
                    "<tr><td>!!</td><td>Блестящий ход</td></tr>"
                    "<tr><td>?</td><td>Ошибка</td></tr>"
                    "<tr><td>??</td><td>Грубая ошибка</td></tr>"
                    "<tr><td>!?</td><td>Интересный ход</td></tr>"
                    "<tr><td>?!</td><td>Сомнительный ход</td></tr>"
                    "</table>",
                    anchor="symbols",
                ),
            ),
            Page(
                anchor="pgn",
                html=wrap_page(
                    "<h1>Формат PGN</h1>"
                    "<p><b>PGN</b> (Portable Game Notation) — стандартный "
                    "текстовый формат записи шахматных партий. Chessie "
                    "поддерживает загрузку и сохранение PGN-файлов.</p>"
                    "<h2>Структура</h2>"
                    "<ol>"
                    "<li><b>Теги</b> (метаданные в квадратных скобках).</li>"
                    "<li><b>Текст ходов</b> (в алгебраической нотации).</li>"
                    "</ol>"
                    '<div class="highlight-box">'
                    '<p style="font-family: monospace; font-size: 12px;">'
                    '[Event "Casual Game"]<br>'
                    '[Site "Internet"]<br>'
                    '[Date "2025.01.15"]<br>'
                    '[White "Alice"]<br>'
                    '[Black "Bob"]<br>'
                    '[Result "1-0"]<br><br>'
                    "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0"
                    "</p>"
                    "</div>"
                    "<h2>Коды результата</h2>"
                    "<ul>"
                    "<li><span class='move'>1-0</span> — победа белых</li>"
                    "<li><span class='move'>0-1</span> — победа чёрных</li>"
                    "<li><span class='move'>1/2-1/2</span> — ничья</li>"
                    "<li><span class='move'>*</span> — партия не окончена</li>"
                    "</ul>"
                    '<div class="note">Используйте <b>Ctrl+O</b> для открытия '
                    "и <b>Ctrl+S</b> для сохранения PGN.</div>",
                    anchor="pgn",
                ),
            ),
        )
        return Chapter(chapter_id=self.chapter_id, title="Нотация", pages=pages)
