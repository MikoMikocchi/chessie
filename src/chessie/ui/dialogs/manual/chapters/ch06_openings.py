"""Chapter 6 – Openings."""

from __future__ import annotations

from chessie.ui.dialogs.manual.chapters._base import fen_diagram, wrap_page
from chessie.ui.dialogs.manual.models import Chapter, ChapterProvider, Page


class OpeningsChapter(ChapterProvider):
    """Opening principles and popular openings."""

    @property
    def chapter_id(self) -> str:
        return "ch06_openings"

    @property
    def order(self) -> int:
        return 60

    def build(self, lang: str) -> Chapter:
        if lang == "Russian":
            return self._build_ru()
        return self._build_en()

    # ── English ──────────────────────────────────────────────────────

    def _build_en(self) -> Chapter:
        pages = (
            Page(
                anchor="principles",
                html=wrap_page(
                    "<h1>Opening Principles</h1>"
                    "<p>The opening is the first phase of the game. Good "
                    "opening play follows three key principles:</p>"
                    "<ol>"
                    "<li><b>Control the centre</b> — place pawns and pieces "
                    "where they control the central squares (e4, d4, e5, d5).</li>"
                    "<li><b>Develop your pieces</b> — bring knights and bishops "
                    "into play early. Don't move the same piece twice without "
                    "good reason.</li>"
                    "<li><b>Castle early</b> — tuck your king to safety and "
                    "connect the rooks.</li>"
                    "</ol>"
                    + fen_diagram(
                        "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R",
                        "A typical opening position after 1.e4 e5 2.Nf3 Nc6",
                    )
                    + '<div class="highlight-box">'
                    "<b>Common mistakes to avoid:</b>"
                    "<ul>"
                    "<li>Moving the queen out too early.</li>"
                    "<li>Moving too many pawns instead of developing pieces.</li>"
                    "<li>Neglecting king safety (forgetting to castle).</li>"
                    "</ul>"
                    "</div>",
                    anchor="principles",
                ),
            ),
            Page(
                anchor="italian",
                html=wrap_page(
                    "<h1>Italian Game</h1>"
                    "<p><span class='move'>1. e4 e5 2. Nf3 Nc6 3. Bc4</span></p>"
                    "<p>The Italian Game is one of the oldest openings. White "
                    "develops the bishop to an active square targeting f7 — "
                    "the weakest point in Black's position.</p>"
                    + fen_diagram(
                        "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R",
                        "Italian Game after 3. Bc4",
                    )
                    + "<h2>Main Ideas</h2>"
                    "<ul>"
                    "<li>White aims for quick development and pressure on f7.</li>"
                    "<li>Common continuations: <span class='move'>3...Bc5</span> "
                    "(Giuoco Piano) or <span class='move'>3...Nf6</span> "
                    "(Two Knights Defense).</li>"
                    "</ul>"
                    '<div class="note">The Italian Game is excellent for '
                    "beginners — it teaches natural development and piece "
                    "coordination.</div>",
                    anchor="italian",
                ),
            ),
            Page(
                anchor="sicilian",
                html=wrap_page(
                    "<h1>Sicilian Defense</h1>"
                    "<p><span class='move'>1. e4 c5</span></p>"
                    "<p>The Sicilian is the <b>most popular defence</b> "
                    "against 1. e4 at all levels. Black immediately fights "
                    "for the centre with a flank pawn.</p>"
                    + fen_diagram(
                        "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR",
                        "Sicilian Defense after 1...c5",
                    )
                    + "<h2>Key Variations</h2>"
                    "<ul>"
                    "<li><b>Open Sicilian</b> (<span class='move'>2. Nf3, "
                    "3. d4</span>) — sharp, tactical play.</li>"
                    "<li><b>Najdorf</b> (<span class='move'>5...a6</span>) — "
                    "the most theoretically deep Sicilian.</li>"
                    "<li><b>Dragon</b> (<span class='move'>5...g6</span>) — "
                    "Black fianchettoes the bishop for a fierce attack.</li>"
                    "</ul>"
                    '<div class="highlight-box">'
                    "The Sicilian leads to asymmetric, combative positions "
                    "where both sides have winning chances."
                    "</div>",
                    anchor="sicilian",
                ),
            ),
            Page(
                anchor="ruy_lopez",
                html=wrap_page(
                    "<h1>Ruy López (Spanish Game)</h1>"
                    "<p><span class='move'>1. e4 e5 2. Nf3 Nc6 3. Bb5</span></p>"
                    "<p>One of the most respected and deeply studied openings. "
                    "The bishop pins the knight that defends the e5 pawn.</p>"
                    + fen_diagram(
                        "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R",
                        "Ruy López after 3. Bb5",
                    )
                    + "<h2>Ideas</h2>"
                    "<ul>"
                    "<li>White pressures the e5 pawn indirectly.</li>"
                    "<li>Black often plays <span class='move'>3...a6</span> "
                    "(Morphy Defense) to question the bishop.</li>"
                    "<li>Rich strategic and tactical play for both sides.</li>"
                    "</ul>"
                    '<div class="note">The Ruy López has been a favourite of '
                    "world champions from Lasker to Carlsen.</div>",
                    anchor="ruy_lopez",
                ),
            ),
            Page(
                anchor="queens_gambit",
                html=wrap_page(
                    "<h1>Queen's Gambit</h1>"
                    "<p><span class='move'>1. d4 d5 2. c4</span></p>"
                    "<p>White offers a pawn to gain central control. Despite "
                    "the name, it is not a true gambit — Black usually cannot "
                    "hold the pawn.</p>"
                    + fen_diagram(
                        "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR",
                        "Queen's Gambit after 2. c4",
                    )
                    + "<h2>Main Responses</h2>"
                    "<ul>"
                    "<li><b>Queen's Gambit Declined</b> "
                    "(<span class='move'>2...e6</span>) — solid, classical.</li>"
                    "<li><b>Queen's Gambit Accepted</b> "
                    "(<span class='move'>2...dxc4</span>) — take and try to "
                    "equalize.</li>"
                    "<li><b>Slav Defense</b> (<span class='move'>2...c6</span>) — "
                    "supports d5 with a pawn.</li>"
                    "</ul>"
                    '<div class="highlight-box">'
                    "The Queen's Gambit is a cornerstone of classical chess, "
                    "emphasizing strategic planning over immediate tactics."
                    "</div>",
                    anchor="queens_gambit",
                ),
            ),
            Page(
                anchor="french",
                html=wrap_page(
                    "<h1>French Defense</h1>"
                    "<p><span class='move'>1. e4 e6</span></p>"
                    "<p>A solid defence where Black plans to challenge the "
                    "centre with <span class='move'>...d5</span> on the next "
                    "move.</p>"
                    + fen_diagram(
                        "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR",
                        "French Defense after 1...e6",
                    )
                    + "<h2>Character</h2>"
                    "<ul>"
                    "<li>Black gets a solid pawn structure but a slightly "
                    "cramped position.</li>"
                    "<li>The light-squared bishop (c8) is often a problem piece — "
                    "it is blocked by the e6 pawn.</li>"
                    "<li>Main lines: Advance (3.e5), Tarrasch (3.Nd2), "
                    "Winawer (3.Nc3 Bb4).</li>"
                    "</ul>"
                    '<div class="note">The French is ideal for players who '
                    "prefer solid, strategic positions and know how to "
                    "transform their structure in the middlegame.</div>",
                    anchor="french",
                ),
            ),
        )
        return Chapter(chapter_id=self.chapter_id, title="Openings", pages=pages)

    # ── Russian ──────────────────────────────────────────────────────

    def _build_ru(self) -> Chapter:
        pages = (
            Page(
                anchor="principles",
                html=wrap_page(
                    "<h1>Принципы дебюта</h1>"
                    "<p>Дебют — начальная фаза партии. Хорошая игра "
                    "в дебюте следует трём правилам:</p>"
                    "<ol>"
                    "<li><b>Контроль центра</b> — ставьте пешки и фигуры "
                    "так, чтобы контролировать e4, d4, e5, d5.</li>"
                    "<li><b>Развитие фигур</b> — выводите коней и слонов "
                    "пораньше. Не двигайте одну фигуру дважды без "
                    "необходимости.</li>"
                    "<li><b>Ранняя рокировка</b> — спрячьте короля "
                    "и соедините ладьи.</li>"
                    "</ol>"
                    + fen_diagram(
                        "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R",
                        "Типичная дебютная позиция после 1.e4 e5 2.Nf3 Nc6",
                    )
                    + '<div class="highlight-box">'
                    "<b>Частые ошибки:</b>"
                    "<ul>"
                    "<li>Ранний вывод ферзя.</li>"
                    "<li>Слишком много пешечных ходов вместо развития.</li>"
                    "<li>Забыть рокироваться.</li>"
                    "</ul>"
                    "</div>",
                    anchor="principles",
                ),
            ),
            Page(
                anchor="italian",
                html=wrap_page(
                    "<h1>Итальянская партия</h1>"
                    "<p><span class='move'>1. e4 e5 2. Nf3 Nc6 3. Bc4</span></p>"
                    "<p>Один из старейших дебютов. Слон выходит на "
                    "активную позицию, нацеливаясь на f7 — слабейший "
                    "пункт у чёрных.</p>"
                    + fen_diagram(
                        "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R",
                        "Итальянская партия после 3. Bc4",
                    )
                    + "<h2>Основные идеи</h2>"
                    "<ul>"
                    "<li>Быстрое развитие и давление на f7.</li>"
                    "<li>Продолжения: <span class='move'>3...Bc5</span> "
                    "(тихая итальянская) или <span class='move'>3...Nf6</span> "
                    "(защита двух коней).</li>"
                    "</ul>"
                    '<div class="note">Отличный дебют для начинающих — '
                    "учит естественному развитию.</div>",
                    anchor="italian",
                ),
            ),
            Page(
                anchor="sicilian",
                html=wrap_page(
                    "<h1>Сицилианская защита</h1>"
                    "<p><span class='move'>1. e4 c5</span></p>"
                    "<p>Самый <b>популярный ответ</b> на 1. e4. Чёрные "
                    "сразу борются за центр фланговой пешкой.</p>"
                    + fen_diagram(
                        "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR",
                        "Сицилианская защита после 1...c5",
                    )
                    + "<h2>Основные варианты</h2>"
                    "<ul>"
                    "<li><b>Открытая сицилианская</b> "
                    "(<span class='move'>2. Nf3, 3. d4</span>).</li>"
                    "<li><b>Найдорф</b> "
                    "(<span class='move'>5...a6</span>).</li>"
                    "<li><b>Дракон</b> "
                    "(<span class='move'>5...g6</span>).</li>"
                    "</ul>"
                    '<div class="highlight-box">'
                    "Сицилианская ведёт к асимметричным, боевым "
                    "позициям."
                    "</div>",
                    anchor="sicilian",
                ),
            ),
            Page(
                anchor="ruy_lopez",
                html=wrap_page(
                    "<h1>Испанская партия (Руй Лопес)</h1>"
                    "<p><span class='move'>1. e4 e5 2. Nf3 Nc6 3. Bb5</span></p>"
                    "<p>Один из наиболее изученных дебютов. Слон связывает "
                    "коня, защищающего e5.</p>"
                    + fen_diagram(
                        "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R",
                        "Испанская партия после 3. Bb5",
                    )
                    + "<h2>Идеи</h2>"
                    "<ul>"
                    "<li>Белые косвенно давят на e5.</li>"
                    "<li>Чёрные часто играют <span class='move'>3...a6</span> "
                    "(защита Морфи).</li>"
                    "</ul>"
                    '<div class="note">Любимый дебют чемпионов мира от '
                    "Ласкера до Карлсена.</div>",
                    anchor="ruy_lopez",
                ),
            ),
            Page(
                anchor="queens_gambit",
                html=wrap_page(
                    "<h1>Ферзевый гамбит</h1>"
                    "<p><span class='move'>1. d4 d5 2. c4</span></p>"
                    "<p>Белые предлагают пешку ради контроля центра.</p>"
                    + fen_diagram(
                        "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR",
                        "Ферзевый гамбит после 2. c4",
                    )
                    + "<h2>Основные ответы</h2>"
                    "<ul>"
                    "<li><b>Отказанный</b> "
                    "(<span class='move'>2...e6</span>).</li>"
                    "<li><b>Принятый</b> "
                    "(<span class='move'>2...dxc4</span>).</li>"
                    "<li><b>Славянская защита</b> "
                    "(<span class='move'>2...c6</span>).</li>"
                    "</ul>"
                    '<div class="highlight-box">'
                    "Краеугольный камень классических шахмат — "
                    "стратегическое планирование важнее быстрых тактик."
                    "</div>",
                    anchor="queens_gambit",
                ),
            ),
            Page(
                anchor="french",
                html=wrap_page(
                    "<h1>Французская защита</h1>"
                    "<p><span class='move'>1. e4 e6</span></p>"
                    "<p>Солидная защита. Чёрные планируют оспорить центр "
                    "ходом <span class='move'>...d5</span>.</p>"
                    + fen_diagram(
                        "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR",
                        "Французская защита после 1...e6",
                    )
                    + "<h2>Характер</h2>"
                    "<ul>"
                    "<li>Прочная пешечная структура, но стеснённая позиция.</li>"
                    "<li>Белопольный слон c8 часто «плохой».</li>"
                    "<li>Основные системы: вариант продвижения (3.e5), "
                    "Тарраш (3.Nd2), Винавер (3.Nc3 Bb4).</li>"
                    "</ul>"
                    '<div class="note">Французская подходит тем, кто '
                    "предпочитает солидные, стратегические позиции.</div>",
                    anchor="french",
                ),
            ),
        )
        return Chapter(chapter_id=self.chapter_id, title="Дебюты", pages=pages)
