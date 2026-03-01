"""Chapter 7 – Endgame Basics."""

from __future__ import annotations

from chessie.ui.dialogs.manual.chapters._base import fen_diagram, wrap_page
from chessie.ui.dialogs.manual.models import Chapter, ChapterProvider, Page


class EndgameChapter(ChapterProvider):
    """Fundamental endgame techniques and checkmates."""

    @property
    def chapter_id(self) -> str:
        return "ch07_endgame"

    @property
    def order(self) -> int:
        return 70

    def build(self, lang: str) -> Chapter:
        if lang == "Russian":
            return self._build_ru()
        return self._build_en()

    # ── English ──────────────────────────────────────────────────────

    def _build_en(self) -> Chapter:
        pages = (
            Page(
                anchor="endgame_principles",
                html=wrap_page(
                    "<h1>Endgame Principles</h1>"
                    "<p>The endgame is the phase of the game when few pieces "
                    "remain. It requires a different mindset from the opening "
                    "and middlegame.</p>"
                    "<h2>Key Principles</h2>"
                    "<ol>"
                    "<li><b>Activate the king</b> — in the endgame the king "
                    "becomes a fighting piece. Bring it to the centre!</li>"
                    "<li><b>Create passed pawns</b> — a pawn with no enemy "
                    "pawns blocking or guarding its path to promotion.</li>"
                    "<li><b>Centralise your pieces</b> — rooks belong on open "
                    "files, behind passed pawns.</li>"
                    "<li><b>Do not rush</b> — endgames reward patience and "
                    "precise calculation.</li>"
                    "</ol>"
                    + fen_diagram(
                        "8/8/4k3/8/4K3/4P3/8/8",
                        "King and pawn endgame — the kings battle for key squares",
                        "d5,e5,f5",
                    )
                    + '<div class="highlight-box">'
                    "Many games are decided in the endgame. Even grandmasters "
                    "study endgame technique extensively."
                    "</div>",
                    anchor="endgame_principles",
                ),
            ),
            Page(
                anchor="kq_vs_k",
                html=wrap_page(
                    "<h1>King + Queen vs. King</h1>"
                    "<p>This is the most basic checkmate. With correct play, "
                    "it is always forced — usually in under 10 moves.</p>"
                    "<h2>Technique</h2>"
                    "<ol>"
                    "<li>Use the queen to restrict the enemy king, pushing it "
                    "toward the edge of the board.</li>"
                    "<li>Bring your own king closer for support.</li>"
                    "<li>Deliver checkmate on the edge or corner.</li>"
                    "</ol>"
                    + fen_diagram(
                        "k7/1Q6/2K5/8/8/8/8/8",
                        "Basic checkmate pattern with king and queen",
                        "a8",
                    )
                    + '<div class="note">Be careful not to accidentally '
                    "stalemate the enemy king! Always leave it at least one "
                    "escape square until you're ready to mate.</div>",
                    anchor="kq_vs_k",
                ),
            ),
            Page(
                anchor="kr_vs_k",
                html=wrap_page(
                    "<h1>King + Rook vs. King</h1>"
                    "<p>Slightly more complex than queen, but still a forced "
                    "win with correct technique.</p>"
                    "<h2>The Box Method</h2>"
                    "<ol>"
                    "<li>Use the rook to create a <b>box</b> (cut off the "
                    "enemy king along a rank or file).</li>"
                    "<li>Bring your king closer, shrinking the box.</li>"
                    "<li>When the enemy king is on the edge, deliver checkmate "
                    "with the rook supported by your king.</li>"
                    "</ol>"
                    + fen_diagram(
                        "k7/2K5/R7/8/8/8/8/8",
                        "Checkmate pattern with king and rook",
                        "a8",
                    )
                    + '<div class="highlight-box">'
                    "Practice this checkmate until you can do it quickly and "
                    "confidently — it appears frequently!"
                    "</div>",
                    anchor="kr_vs_k",
                ),
            ),
            Page(
                anchor="opposition",
                html=wrap_page(
                    "<h1>Opposition &amp; Key Squares</h1>"
                    "<p><b>Opposition</b> is when two kings face each other "
                    "with one square between them. The player <em>not</em> "
                    "to move has the opposition — a crucial advantage in king "
                    "and pawn endgames.</p>"
                    + fen_diagram(
                        "8/8/4k3/8/4K3/8/4P3/8",
                        "White has the opposition (Black to move)",
                        "e4,e6",
                    )
                    + "<p>With the opposition, White's king can advance and "
                    "support the pawn to promotion.</p>"
                    "<h2>Key Squares</h2>"
                    "<p>For a pawn on a given square, there are <b>key squares"
                    "</b> that the king must reach to guarantee promotion:</p>"
                    "<ul>"
                    "<li>A pawn on e4 has key squares "
                    "<b>d5, e5, f5, d6, e6, f6</b>.</li>"
                    "<li>If the attacking king reaches a key square, the pawn "
                    "promotes regardless of the defender's play.</li>"
                    "</ul>"
                    '<div class="note">Learning key squares and opposition '
                    "is the foundation of all pawn endgames.</div>",
                    anchor="opposition",
                ),
            ),
            Page(
                anchor="stalemate_danger",
                html=wrap_page(
                    "<h1>Stalemate Danger</h1>"
                    "<p><b>Stalemate</b> occurs when the side to move has no "
                    "legal moves and is <em>not</em> in check. The game is "
                    "immediately drawn.</p>"
                    + fen_diagram(
                        "k7/2Q5/1K6/8/8/8/8/8",
                        "Stalemate — Black has no legal moves but is not in check!",
                    )
                    + '<div class="highlight-box">'
                    "<b>Common stalemate traps:</b>"
                    "<ul>"
                    "<li>Your queen controls too many squares around the enemy "
                    "king — leave an escape!</li>"
                    "<li>In rook endgames, pushing the enemy king into a corner "
                    "without checking can stalemate.</li>"
                    "<li>When you're winning, always ask: «Does my opponent "
                    "have any legal move?»</li>"
                    "</ul>"
                    "</div>"
                    '<div class="note">When you are <em>losing</em>, stalemate '
                    "is your best friend! Look for ways to eliminate all your "
                    "legal moves to save a draw.</div>",
                    anchor="stalemate_danger",
                ),
            ),
        )
        return Chapter(chapter_id=self.chapter_id, title="Endgame", pages=pages)

    # ── Russian ──────────────────────────────────────────────────────

    def _build_ru(self) -> Chapter:
        pages = (
            Page(
                anchor="endgame_principles",
                html=wrap_page(
                    "<h1>Принципы эндшпиля</h1>"
                    "<p>Эндшпиль — фаза партии с малым количеством "
                    "фигур. Требует иного мышления.</p>"
                    "<h2>Ключевые принципы</h2>"
                    "<ol>"
                    "<li><b>Активизируйте короля</b> — в эндшпиле "
                    "король становится боевой фигурой. Ведите его "
                    "в центр!</li>"
                    "<li><b>Создавайте проходные пешки</b> — пешку, "
                    "путь которой к превращению не блокирован.</li>"
                    "<li><b>Централизуйте фигуры</b> — ладьи на "
                    "открытых вертикалях, за проходными.</li>"
                    "<li><b>Не спешите</b> — эндшпиль вознаграждает "
                    "терпение и точный расчёт.</li>"
                    "</ol>"
                    + fen_diagram(
                        "8/8/4k3/8/4K3/4P3/8/8",
                        "Пешечный эндшпиль — короли борются за ключевые поля",
                        "d5,e5,f5",
                    )
                    + '<div class="highlight-box">'
                    "Многие партии решаются в эндшпиле. Даже "
                    "гроссмейстеры уделяют его изучению много времени."
                    "</div>",
                    anchor="endgame_principles",
                ),
            ),
            Page(
                anchor="kq_vs_k",
                html=wrap_page(
                    "<h1>Король + Ферзь vs. Король</h1>"
                    "<p>Базовый мат. При правильной игре форсируется "
                    "менее чем за 10 ходов.</p>"
                    "<h2>Техника</h2>"
                    "<ol>"
                    "<li>Ферзём оттесняйте вражеского короля к краю.</li>"
                    "<li>Приблизьте своего короля.</li>"
                    "<li>Ставьте мат на краю доски.</li>"
                    "</ol>"
                    + fen_diagram(
                        "k7/1Q6/2K5/8/8/8/8/8",
                        "Базовый мат ферзём при поддержке короля",
                        "a8",
                    )
                    + '<div class="note">Не допустите пата! Оставляйте '
                    "королю хотя бы одно поле, пока не готовы матовать."
                    "</div>",
                    anchor="kq_vs_k",
                ),
            ),
            Page(
                anchor="kr_vs_k",
                html=wrap_page(
                    "<h1>Король + Ладья vs. Король</h1>"
                    "<p>Чуть сложнее мата ферзём, но всё равно "
                    "выигрывается.</p>"
                    "<h2>Метод коробки</h2>"
                    "<ol>"
                    "<li>Ладьёй отрезайте вражеского короля вдоль "
                    "горизонтали или вертикали.</li>"
                    "<li>Приближайте своего короля, сужая «коробку».</li>"
                    "<li>Ставьте мат на краю при поддержке своего "
                    "короля.</li>"
                    "</ol>"
                    + fen_diagram(
                        "k7/2K5/R7/8/8/8/8/8",
                        "Базовая матовая сетка ладьёй",
                        "a8",
                    )
                    + '<div class="highlight-box">'
                    "Отрабатывайте этот мат до автоматизма — он "
                    "встречается часто!"
                    "</div>",
                    anchor="kr_vs_k",
                ),
            ),
            Page(
                anchor="opposition",
                html=wrap_page(
                    "<h1>Оппозиция и ключевые поля</h1>"
                    "<p><b>Оппозиция</b> — положение, когда короли "
                    "стоят друг напротив друга через одну клетку. "
                    "Игрок, <em>не</em> имеющий хода, владеет "
                    "оппозицией.</p>"
                    + fen_diagram(
                        "8/8/4k3/8/4K3/8/4P3/8",
                        "У белых оппозиция (ход чёрных)",
                        "e4,e6",
                    )
                    + "<p>С оппозицией белый король продвигается "
                    "и проводит пешку.</p>"
                    "<h2>Ключевые поля</h2>"
                    "<ul>"
                    "<li>Пешка на e4 имеет ключевые поля "
                    "<b>d5, e5, f5, d6, e6, f6</b>.</li>"
                    "<li>Если атакующий король достигает ключевого "
                    "поля — пешка проходит.</li>"
                    "</ul>"
                    '<div class="note">Ключевые поля и оппозиция — '
                    "фундамент всех пешечных эндшпилей.</div>",
                    anchor="opposition",
                ),
            ),
            Page(
                anchor="stalemate_danger",
                html=wrap_page(
                    "<h1>Опасность пата</h1>"
                    "<p><b>Пат</b> — ситуация, когда у стороны с ходом "
                    "нет легальных ходов, но король <em>не</em> под шахом. "
                    "Партия тут же признаётся ничьей.</p>"
                    + fen_diagram(
                        "k7/2Q5/1K6/8/8/8/8/8",
                        "Пат — у чёрных нет ходов, но шаха нет!",
                    )
                    + '<div class="highlight-box">'
                    "<b>Типичные ловушки пата:</b>"
                    "<ul>"
                    "<li>Ферзь контролирует слишком много полей вокруг "
                    "короля — оставьте выход!</li>"
                    "<li>В ладейных эндшпилях — загон короля в угол "
                    "без шаха.</li>"
                    "<li>Всегда проверяйте: «есть ли у соперника "
                    "легальный ход?»</li>"
                    "</ul>"
                    "</div>"
                    '<div class="note">Если вы <em>проигрываете</em>, пат — '
                    "ваш лучший друг!</div>",
                    anchor="stalemate_danger",
                ),
            ),
        )
        return Chapter(chapter_id=self.chapter_id, title="Эндшпиль", pages=pages)
