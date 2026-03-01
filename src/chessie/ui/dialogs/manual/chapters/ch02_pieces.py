"""Chapter 2 – How the Pieces Move."""

from __future__ import annotations

from chessie.ui.dialogs.manual.chapters._base import fen_diagram, wrap_page
from chessie.ui.dialogs.manual.models import Chapter, ChapterProvider, Page


class PiecesChapter(ChapterProvider):
    """Movement rules for every chess piece."""

    @property
    def chapter_id(self) -> str:
        return "ch02_pieces"

    @property
    def order(self) -> int:
        return 20

    def build(self, lang: str) -> Chapter:
        if lang == "Russian":
            return self._build_ru()
        return self._build_en()

    # ── English ──────────────────────────────────────────────────────

    def _build_en(self) -> Chapter:
        pages = (
            # King
            Page(
                anchor="king",
                html=wrap_page(
                    "<h1>The King ♔</h1>"
                    "<p>The king is the most important piece. If your king is "
                    "checkmated, you lose the game.</p>"
                    "<p>The king moves <b>one square</b> in any direction — "
                    "horizontally, vertically, or diagonally.</p>"
                    + fen_diagram(
                        "8/8/8/3K4/8/8/8/8",
                        "The king can move to any adjacent square",
                        "c6,d6,e6,c5,e5,c4,d4,e4",
                    )
                    + '<div class="highlight-box">'
                    "The king may <b>never</b> move to a square that is "
                    "attacked by an enemy piece. It also cannot stay on a "
                    "square where it is in check."
                    "</div>"
                    "<p>Despite limited mobility, the king becomes a powerful "
                    "piece in the endgame when fewer threats remain on the "
                    "board.</p>",
                    anchor="king",
                ),
            ),
            # Queen
            Page(
                anchor="queen",
                html=wrap_page(
                    "<h1>The Queen ♕</h1>"
                    "<p>The queen is the most powerful piece. She combines the "
                    "movement of the rook and bishop.</p>"
                    "<p>The queen can move any number of squares in a straight "
                    "line — <b>horizontally, vertically, or diagonally</b> — as "
                    "long as no piece blocks her path.</p>"
                    + fen_diagram(
                        "8/8/8/3Q4/8/8/8/8",
                        "The queen controls ranks, files and diagonals",
                        "a5,b5,c5,e5,f5,g5,h5,d1,d2,d3,d4,d6,d7,d8,"
                        "c6,b7,a8,e6,f7,g8,c4,b3,a2,e4,f3,g2,h1",
                    )
                    + '<div class="note">Because the queen is so valuable '
                    "(≈ 9 points), losing her early usually leads to defeat. "
                    "Protect your queen!</div>"
                    "<p>The queen excels at both attack and defence and is "
                    "often the key piece in tactical combinations.</p>"
                    "<h2>Practical Tips</h2>"
                    "<ul>"
                    "<li>In the opening, avoid early queen adventures unless "
                    "you gain concrete tempo or material.</li>"
                    "<li>Coordinate the queen with minor pieces for tactical "
                    "threats on weak squares (f7/f2, pinned pieces).</li>"
                    "<li>In the endgame, centralize the queen and keep your "
                    "king safe from perpetual checks.</li>"
                    "</ul>",
                    anchor="queen",
                ),
            ),
            # Rook
            Page(
                anchor="rook",
                html=wrap_page(
                    "<h1>The Rook ♖</h1>"
                    "<p>The rook moves any number of squares along a "
                    "<b>rank or file</b> (horizontally or vertically), as "
                    "long as no piece is in the way.</p>"
                    + fen_diagram(
                        "8/8/8/3R4/8/8/8/8",
                        "The rook controls its rank and file",
                        "a5,b5,c5,e5,f5,g5,h5,d1,d2,d3,d4,d6,d7,d8",
                    )
                    + "<p>Each player starts with <b>two rooks</b>, placed "
                    "in the corners of the board.</p>"
                    '<div class="highlight-box">'
                    "<b>Value:</b> a rook is worth approximately <b>5 points"
                    "</b>. Two rooks working together are very powerful, "
                    "especially on open files."
                    "</div>"
                    "<h2>Rook Fundamentals</h2>"
                    "<ul>"
                    "<li>Place rooks on <b>open files</b> to invade the 7th rank.</li>"
                    "<li>Doubling rooks on one file often creates decisive pressure.</li>"
                    "<li>Rooks are strongest <b>behind passed pawns</b> in endgames.</li>"
                    "</ul>"
                    "<p>Rooks are also involved in "
                    '<a href="manual:ch03_special#castling">castling</a>.</p>',
                    anchor="rook",
                ),
            ),
            # Bishop
            Page(
                anchor="bishop",
                html=wrap_page(
                    "<h1>The Bishop ♗</h1>"
                    "<p>The bishop moves any number of squares "
                    "<b>diagonally</b>, as long as no piece blocks the way.</p>"
                    + fen_diagram(
                        "8/8/8/3B4/8/8/8/8",
                        "The bishop moves along diagonals",
                        "c6,b7,a8,e6,f7,g8,c4,b3,a2,e4,f3,g2,h1",
                    )
                    + "<p>Because it only moves diagonally, a bishop is "
                    "forever confined to squares of one colour. Each side "
                    "starts with <b>two bishops</b> — one on light squares, "
                    "one on dark squares.</p>"
                    '<div class="highlight-box">'
                    "<b>Value:</b> ≈ 3 points. The <b>bishop pair</b> (both "
                    "bishops together) is especially strong because it covers "
                    "all colours."
                    "</div>"
                    "<h2>Good vs. Bad Bishop</h2>"
                    "<ul>"
                    "<li>A bishop is usually <b>good</b> when your pawns sit on "
                    "the opposite colour squares.</li>"
                    "<li>A bishop is often <b>bad</b> when blocked by your own "
                    "pawns on the same colour.</li>"
                    "<li>In open positions, bishops often outperform knights.</li>"
                    "</ul>",
                    anchor="bishop",
                ),
            ),
            # Knight
            Page(
                anchor="knight",
                html=wrap_page(
                    "<h1>The Knight ♘</h1>"
                    "<p>The knight has the most unusual movement. It jumps in "
                    "an <b>L-shape</b>: two squares in one direction, then one "
                    "square perpendicular (or vice versa).</p>"
                    + fen_diagram(
                        "8/8/8/3N4/8/8/8/8",
                        "All possible knight moves from d5",
                        "c7,e7,b6,f6,b4,f4,c3,e3",
                    )
                    + '<div class="highlight-box">'
                    "The knight is the <b>only</b> piece that can jump over "
                    "other pieces. It is not blocked by pieces standing in "
                    "its path."
                    "</div>"
                    "<p><b>Value:</b> ≈ 3 points. Knights excel in closed "
                    "positions where their ability to jump is most useful. "
                    "A knight on a strong outpost in the centre can dominate "
                    "the position.</p>"
                    '<div class="note">A knight always changes square colour '
                    "with each move.</div>",
                    anchor="knight",
                ),
            ),
            # Pawn
            Page(
                anchor="pawn",
                html=wrap_page(
                    "<h1>The Pawn ♙</h1>"
                    "<p>Pawns are the most numerous pieces (8 per side) and "
                    "have unique movement rules:</p>"
                    "<ul>"
                    "<li><b>Advance:</b> one square forward (toward the "
                    "opponent's side).</li>"
                    "<li><b>First move:</b> optionally two squares forward.</li>"
                    "<li><b>Capture:</b> one square diagonally forward.</li>"
                    "</ul>"
                    + fen_diagram(
                        "8/8/8/8/8/2n5/3P4/8",
                        "The pawn on d2 can move to d3, d4, or capture on c3",
                        "d3,d4,c3",
                    )
                    + "<p><b>Value:</b> 1 point (the basic unit of material "
                    "value).</p>"
                    '<div class="note">Pawns cannot move backward! This makes '
                    "every pawn move a permanent decision. See also: "
                    '<a href="manual:ch03_special#en_passant">en passant</a> '
                    "and "
                    '<a href="manual:ch03_special#promotion">promotion</a>.'
                    "</div>",
                    anchor="pawn",
                ),
            ),
            # Piece values summary
            Page(
                anchor="piece_values",
                html=wrap_page(
                    "<h1>Piece Values</h1>"
                    "<p>Knowing the approximate value of each piece helps "
                    "you make good trades:</p>"
                    "<table>"
                    "<tr><th>Piece</th><th>Symbol</th><th>Value</th></tr>"
                    "<tr><td>Pawn</td><td>♙</td><td>1</td></tr>"
                    "<tr><td>Knight</td><td>♘</td><td>3</td></tr>"
                    "<tr><td>Bishop</td><td>♗</td><td>3</td></tr>"
                    "<tr><td>Rook</td><td>♖</td><td>5</td></tr>"
                    "<tr><td>Queen</td><td>♕</td><td>9</td></tr>"
                    "<tr><td>King</td><td>♔</td><td>∞</td></tr>"
                    "</table>"
                    '<div class="highlight-box">'
                    "These values are <em>guidelines</em>. Position, pawn "
                    "structure, and piece activity can make a piece worth "
                    "more or less than its nominal value."
                    "</div>"
                    "<p>For example, a bishop in an open position is often "
                    "stronger than a knight, while a knight in a closed, "
                    "blocked position may outperform a bishop.</p>",
                    anchor="piece_values",
                ),
            ),
        )
        return Chapter(chapter_id=self.chapter_id, title="The Pieces", pages=pages)

    # ── Russian ──────────────────────────────────────────────────────

    def _build_ru(self) -> Chapter:
        pages = (
            Page(
                anchor="king",
                html=wrap_page(
                    "<h1>Король ♔</h1>"
                    "<p>Король — важнейшая фигура. Если вашему королю "
                    "поставлен мат, вы проиграли.</p>"
                    "<p>Король ходит на <b>одну клетку</b> в любом "
                    "направлении — по горизонтали, вертикали или "
                    "диагонали.</p>"
                    + fen_diagram(
                        "8/8/8/3K4/8/8/8/8",
                        "Король может пойти на любую соседнюю клетку",
                        "c6,d6,e6,c5,e5,c4,d4,e4",
                    )
                    + '<div class="highlight-box">'
                    "Король <b>никогда</b> не может ходить на поле, "
                    "атакованное фигурой противника."
                    "</div>"
                    "<p>Несмотря на ограниченную подвижность, в эндшпиле "
                    "король становится мощной фигурой.</p>",
                    anchor="king",
                ),
            ),
            Page(
                anchor="queen",
                html=wrap_page(
                    "<h1>Ферзь ♕</h1>"
                    "<p>Ферзь — самая сильная фигура. Она сочетает ходы "
                    "ладьи и слона.</p>"
                    "<p>Ферзь перемещается на любое число клеток по "
                    "<b>горизонтали, вертикали или диагонали</b>, если "
                    "путь не преграждён.</p>"
                    + fen_diagram(
                        "8/8/8/3Q4/8/8/8/8",
                        "Ферзь контролирует горизонтали, вертикали и диагонали",
                        "a5,b5,c5,e5,f5,g5,h5,d1,d2,d3,d4,d6,d7,d8,"
                        "c6,b7,a8,e6,f7,g8,c4,b3,a2,e4,f3,g2,h1",
                    )
                    + '<div class="note">Ферзь стоит ≈ 9 очков. Потеря ферзя '
                    "в начале партии обычно ведёт к поражению.</div>"
                    "<p>Ферзь одновременно силён в атаке и защите, особенно "
                    "в тактических позициях.</p>"
                    "<h2>Практические советы</h2>"
                    "<ul>"
                    "<li>В дебюте не выводите ферзя слишком рано без тактической "
                    "выгоды.</li>"
                    "<li>Связывайте ферзя с лёгкими фигурами для атак на слабые "
                    "поля (f7/f2, связки, двойные удары).</li>"
                    "<li>В эндшпиле централизуйте ферзя и избегайте вечного шаха "
                    "со стороны соперника.</li>"
                    "</ul>",
                    anchor="queen",
                ),
            ),
            Page(
                anchor="rook",
                html=wrap_page(
                    "<h1>Ладья ♖</h1>"
                    "<p>Ладья ходит на любое количество клеток по "
                    "<b>горизонтали или вертикали</b>.</p>"
                    + fen_diagram(
                        "8/8/8/3R4/8/8/8/8",
                        "Ладья контролирует горизонталь и вертикаль",
                        "a5,b5,c5,e5,f5,g5,h5,d1,d2,d3,d4,d6,d7,d8",
                    )
                    + "<p>У каждого игрока <b>две ладьи</b>, стоящие "
                    "по углам доски.</p>"
                    '<div class="highlight-box">'
                    "<b>Ценность:</b> ≈ 5 очков. Пара ладей на открытых "
                    "вертикалях — грозная сила."
                    "</div>"
                    "<h2>Базовые принципы игры ладьёй</h2>"
                    "<ul>"
                    "<li>Ставьте ладьи на <b>открытые вертикали</b> и вторгайтесь "
                    "на 7-ю горизонталь.</li>"
                    "<li>Удвоенные ладьи по одной вертикали часто создают "
                    "решающее давление.</li>"
                    "<li>В эндшпиле ладья сильнее всего <b>за проходной пешкой</b>.</li>"
                    "</ul>"
                    "<p>Ладья также участвует в "
                    '<a href="manual:ch03_special#castling">рокировке</a>.'
                    "</p>",
                    anchor="rook",
                ),
            ),
            Page(
                anchor="bishop",
                html=wrap_page(
                    "<h1>Слон ♗</h1>"
                    "<p>Слон ходит на любое число клеток по "
                    "<b>диагонали</b>.</p>"
                    + fen_diagram(
                        "8/8/8/3B4/8/8/8/8",
                        "Слон движется по диагоналям",
                        "c6,b7,a8,e6,f7,g8,c4,b3,a2,e4,f3,g2,h1",
                    )
                    + "<p>Слон навсегда привязан к клеткам одного цвета. "
                    "У каждой стороны два слона — белопольный и "
                    "чернопольный.</p>"
                    '<div class="highlight-box">'
                    "<b>Ценность:</b> ≈ 3 очка. <b>Два слона</b> вместе "
                    "особенно сильны, контролируя все цвета."
                    "</div>"
                    "<h2>«Хороший» и «плохой» слон</h2>"
                    "<ul>"
                    "<li>Слон обычно <b>хороший</b>, если ваши пешки стоят на "
                    "клетках противоположного цвета.</li>"
                    "<li>Слон часто <b>плохой</b>, если упирается в свои пешки "
                    "на клетках его цвета.</li>"
                    "<li>В открытых позициях слоны нередко сильнее коней.</li>"
                    "</ul>",
                    anchor="bishop",
                ),
            ),
            Page(
                anchor="knight",
                html=wrap_page(
                    "<h1>Конь ♘</h1>"
                    "<p>Конь ходит <b>буквой «Г»</b>: два поля в одном "
                    "направлении и одно перпендикулярно (или наоборот).</p>"
                    + fen_diagram(
                        "8/8/8/3N4/8/8/8/8",
                        "Все возможные ходы коня с d5",
                        "c7,e7,b6,f6,b4,f4,c3,e3",
                    )
                    + '<div class="highlight-box">'
                    "Конь — <b>единственная</b> фигура, способная "
                    "перепрыгивать другие фигуры."
                    "</div>"
                    "<p><b>Ценность:</b> ≈ 3 очка. Конь особенно силён в "
                    "закрытых позициях.</p>"
                    '<div class="note">Конь при каждом ходе меняет цвет '
                    "поля.</div>",
                    anchor="knight",
                ),
            ),
            Page(
                anchor="pawn",
                html=wrap_page(
                    "<h1>Пешка ♙</h1>"
                    "<p>У каждой стороны 8 пешек с особыми правилами:</p>"
                    "<ul>"
                    "<li><b>Ход:</b> на одну клетку вперёд.</li>"
                    "<li><b>Первый ход:</b> можно на две клетки.</li>"
                    "<li><b>Взятие:</b> на одну клетку по диагонали вперёд.</li>"
                    "</ul>"
                    + fen_diagram(
                        "8/8/8/8/8/2n5/3P4/8",
                        "Пешка d2 может пойти на d3, d4 или побить на c3",
                        "d3,d4,c3",
                    )
                    + "<p><b>Ценность:</b> 1 очко.</p>"
                    '<div class="note">Пешки не ходят назад! См. также: '
                    '<a href="manual:ch03_special#en_passant">взятие на проходе</a>'
                    " и "
                    '<a href="manual:ch03_special#promotion">превращение</a>.'
                    "</div>",
                    anchor="pawn",
                ),
            ),
            Page(
                anchor="piece_values",
                html=wrap_page(
                    "<h1>Ценность фигур</h1>"
                    "<p>Приблизительная ценность помогает оценивать "
                    "размены:</p>"
                    "<table>"
                    "<tr><th>Фигура</th><th>Символ</th><th>Очки</th></tr>"
                    "<tr><td>Пешка</td><td>♙</td><td>1</td></tr>"
                    "<tr><td>Конь</td><td>♘</td><td>3</td></tr>"
                    "<tr><td>Слон</td><td>♗</td><td>3</td></tr>"
                    "<tr><td>Ладья</td><td>♖</td><td>5</td></tr>"
                    "<tr><td>Ферзь</td><td>♕</td><td>9</td></tr>"
                    "<tr><td>Король</td><td>♔</td><td>∞</td></tr>"
                    "</table>"
                    '<div class="highlight-box">'
                    "Это ориентиры. Позиция, пешечная структура и "
                    "активность фигур могут менять реальную ценность."
                    "</div>",
                    anchor="piece_values",
                ),
            ),
        )
        return Chapter(chapter_id=self.chapter_id, title="Фигуры", pages=pages)
