"""Chapter 3 – Special Moves."""

from __future__ import annotations

from chessie.ui.dialogs.manual.chapters._base import fen_diagram, wrap_page
from chessie.ui.dialogs.manual.models import Chapter, ChapterProvider, Page


class SpecialMovesChapter(ChapterProvider):
    """Castling, en passant, and pawn promotion."""

    @property
    def chapter_id(self) -> str:
        return "ch03_special"

    @property
    def order(self) -> int:
        return 30

    def build(self, lang: str) -> Chapter:
        if lang == "Russian":
            return self._build_ru()
        return self._build_en()

    # ── English ──────────────────────────────────────────────────────

    def _build_en(self) -> Chapter:
        pages = (
            Page(
                anchor="castling",
                html=wrap_page(
                    "<h1>Castling</h1>"
                    "<p>Castling is a special king move that also repositions "
                    "a rook. It is the only move that moves two pieces at "
                    "once.</p>"
                    "<h2>Kingside Castling (O-O)</h2>"
                    "<p>The king moves two squares toward the h-rook, and the "
                    "rook jumps to the other side of the king.</p>"
                    + fen_diagram(
                        "8/8/8/8/8/8/8/4K2R",
                        "Before kingside castling",
                        "e1,g1",
                    )
                    + fen_diagram(
                        "8/8/8/8/8/8/8/5RK1",
                        "After kingside castling (O-O)",
                    )
                    + "<h2>Queenside Castling (O-O-O)</h2>"
                    "<p>The king moves two squares toward the a-rook.</p>"
                    + fen_diagram(
                        "8/8/8/8/8/8/8/R3K3",
                        "Before queenside castling",
                        "e1,c1",
                    )
                    + fen_diagram(
                        "8/8/8/8/8/8/8/2KR4",
                        "After queenside castling (O-O-O)",
                    ),
                    anchor="castling",
                ),
            ),
            Page(
                anchor="castling_rules",
                html=wrap_page(
                    "<h1>Castling Conditions</h1>"
                    "<p>Castling is only allowed when <b>all</b> of the "
                    "following conditions are met:</p>"
                    "<ol>"
                    "<li>The king has <b>not</b> moved previously.</li>"
                    "<li>The rook involved has <b>not</b> moved previously.</li>"
                    "<li>There are <b>no pieces</b> between king and rook.</li>"
                    "<li>The king is <b>not in check</b>.</li>"
                    "<li>The king does <b>not pass through</b> a square "
                    "attacked by an enemy piece.</li>"
                    "<li>The king does <b>not land on</b> an attacked square.</li>"
                    "</ol>"
                    '<div class="note">The rook <em>may</em> pass through an '
                    "attacked square during queenside castling — only the "
                    "king's path matters.</div>"
                    '<div class="highlight-box">'
                    "Castling is a vital defensive and developmental move. "
                    "It tucks the king into safety and activates the rook."
                    "</div>",
                    anchor="castling_rules",
                ),
            ),
            Page(
                anchor="en_passant",
                html=wrap_page(
                    "<h1>En Passant</h1>"
                    "<p><em>En passant</em> (French: «in passing») is a special "
                    "pawn capture. It can occur when a pawn advances two squares "
                    "from its starting position and lands beside an enemy pawn.</p>"
                    "<p>The enemy pawn may capture it <b>as if</b> it had only "
                    "moved one square forward. This capture must be done "
                    "<b>immediately</b> — on the very next move — or the right "
                    "is lost.</p>"
                    + fen_diagram(
                        "8/8/8/3Pp3/8/8/8/8",
                        "Black just played e7–e5. White can capture en passant.",
                        "e6",
                    )
                    + fen_diagram(
                        "8/8/4P3/8/8/8/8/8",
                        "After dxe6 en passant",
                    )
                    + '<div class="highlight-box">'
                    "En passant exists to prevent a pawn from using its "
                    "double-push to safely pass an enemy pawn."
                    "</div>",
                    anchor="en_passant",
                ),
            ),
            Page(
                anchor="promotion",
                html=wrap_page(
                    "<h1>Pawn Promotion</h1>"
                    "<p>When a pawn reaches the <b>last rank</b> (rank 8 for "
                    "White, rank 1 for Black), it must be <b>promoted</b> to "
                    "another piece: queen, rook, bishop, or knight.</p>"
                    + fen_diagram(
                        "8/3P4/8/8/8/8/8/8",
                        "White's pawn is about to promote",
                        "d8",
                    )
                    + "<p>In most cases, players promote to a <b>queen</b> "
                    "(the strongest piece). Promoting to a different piece is "
                    "called <b>underpromotion</b>.</p>"
                    '<div class="note">Sometimes promoting to a knight is the '
                    "best move — for example, to deliver a check that a queen "
                    "couldn't give!</div>"
                    '<div class="highlight-box">'
                    "There is no limit to the number of queens (or other pieces) "
                    "you can have. It is theoretically possible to have 9 queens."
                    "</div>",
                    anchor="promotion",
                ),
            ),
        )
        return Chapter(chapter_id=self.chapter_id, title="Special Moves", pages=pages)

    # ── Russian ──────────────────────────────────────────────────────

    def _build_ru(self) -> Chapter:
        pages = (
            Page(
                anchor="castling",
                html=wrap_page(
                    "<h1>Рокировка</h1>"
                    "<p>Рокировка — особый ход короля, при котором также "
                    "перемещается ладья. Это единственный ход, "
                    "двигающий две фигуры разом.</p>"
                    "<h2>Короткая рокировка (O-O)</h2>"
                    "<p>Король перемещается на два поля в сторону ладьи h, "
                    "а ладья перепрыгивает через него.</p>"
                    + fen_diagram(
                        "8/8/8/8/8/8/8/4K2R",
                        "До короткой рокировки",
                        "e1,g1",
                    )
                    + fen_diagram(
                        "8/8/8/8/8/8/8/5RK1",
                        "После O-O",
                    )
                    + "<h2>Длинная рокировка (O-O-O)</h2>"
                    "<p>Король перемещается на два поля в сторону ладьи a.</p>"
                    + fen_diagram(
                        "8/8/8/8/8/8/8/R3K3",
                        "До длинной рокировки",
                        "e1,c1",
                    )
                    + fen_diagram(
                        "8/8/8/8/8/8/8/2KR4",
                        "После O-O-O",
                    ),
                    anchor="castling",
                ),
            ),
            Page(
                anchor="castling_rules",
                html=wrap_page(
                    "<h1>Условия рокировки</h1>"
                    "<p>Рокировка разрешена, только если выполнены <b>все</b> "
                    "условия:</p>"
                    "<ol>"
                    "<li>Король <b>не ходил</b> ранее.</li>"
                    "<li>Соответствующая ладья <b>не ходила</b> ранее.</li>"
                    "<li>Между королём и ладьёй <b>нет фигур</b>.</li>"
                    "<li>Король <b>не под шахом</b>.</li>"
                    "<li>Король <b>не проходит</b> через атакованное поле.</li>"
                    "<li>Король <b>не попадает</b> на атакованное поле.</li>"
                    "</ol>"
                    '<div class="note">При длинной рокировке ладья <em>может</em> '
                    "проходить через атакованное поле — важен лишь путь "
                    "короля.</div>"
                    '<div class="highlight-box">'
                    "Рокировка — ключевой ход для безопасности короля и "
                    "активации ладьи."
                    "</div>",
                    anchor="castling_rules",
                ),
            ),
            Page(
                anchor="en_passant",
                html=wrap_page(
                    "<h1>Взятие на проходе</h1>"
                    "<p><em>En passant</em> (фр. «на проходе») — особое "
                    "взятие пешкой. Если пешка противника продвинулась на "
                    "два поля со стартовой позиции и встала рядом с вашей "
                    "пешкой, вы можете побить её <b>так, как будто</b> она "
                    "прошла одно поле.</p>"
                    "<p>Это взятие нужно совершить <b>немедленно</b> — на "
                    "следующем же ходу, иначе право теряется.</p>"
                    + fen_diagram(
                        "8/8/8/3Pp3/8/8/8/8",
                        "Чёрные сыграли e7–e5. Белые могут взять на проходе.",
                        "e6",
                    )
                    + fen_diagram(
                        "8/8/4P3/8/8/8/8/8",
                        "После dxe6 на проходе",
                    )
                    + '<div class="highlight-box">'
                    "Взятие на проходе не позволяет пешке «проскочить» мимо "
                    "пешки противника двойным ходом."
                    "</div>",
                    anchor="en_passant",
                ),
            ),
            Page(
                anchor="promotion",
                html=wrap_page(
                    "<h1>Превращение пешки</h1>"
                    "<p>Когда пешка достигает <b>последнего ряда</b> "
                    "(8-го для белых, 1-го для чёрных), она обязана "
                    "<b>превратиться</b> в другую фигуру: ферзя, ладью, "
                    "слона или коня.</p>"
                    + fen_diagram(
                        "8/3P4/8/8/8/8/8/8",
                        "Белая пешка готова к превращению",
                        "d8",
                    )
                    + "<p>Чаще всего выбирают <b>ферзя</b>. Превращение в "
                    "другую фигуру называют «недопревращением».</p>"
                    '<div class="note">Иногда лучший ход — превращение в коня, '
                    "например для шаха, который ферзь не мог бы дать!</div>"
                    '<div class="highlight-box">'
                    "Количество ферзей (и других фигур) не ограничено. "
                    "Теоретически можно иметь 9 ферзей."
                    "</div>",
                    anchor="promotion",
                ),
            ),
        )
        return Chapter(chapter_id=self.chapter_id, title="Особые ходы", pages=pages)
