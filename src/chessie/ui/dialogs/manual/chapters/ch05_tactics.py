"""Chapter 5 – Tactics."""

from __future__ import annotations

from chessie.ui.dialogs.manual.chapters._base import fen_diagram, wrap_page
from chessie.ui.dialogs.manual.models import Chapter, ChapterProvider, Page


class TacticsChapter(ChapterProvider):
    """Forks, pins, skewers, discovered attacks, sacrifices."""

    @property
    def chapter_id(self) -> str:
        return "ch05_tactics"

    @property
    def order(self) -> int:
        return 50

    def build(self, lang: str) -> Chapter:
        if lang == "Russian":
            return self._build_ru()
        return self._build_en()

    # ── English ──────────────────────────────────────────────────────

    def _build_en(self) -> Chapter:
        pages = (
            Page(
                anchor="forks",
                html=wrap_page(
                    "<h1>Forks</h1>"
                    "<p>A <b>fork</b> is a move where one piece attacks "
                    "<b>two or more</b> enemy pieces simultaneously. The "
                    "opponent can only save one of them.</p>"
                    "<h2>Knight Fork</h2>"
                    "<p>Knights are the most common forking pieces because "
                    "their L-shaped movement can hit multiple targets.</p>"
                    + fen_diagram(
                        "8/2r1k3/8/3N4/8/8/8/4K3",
                        "The knight on d5 forks the king on e7 and rook on c7",
                        "d5,e7,c7",
                    )
                    + "<h2>Other Forks</h2>"
                    "<p>Any piece can fork. Pawns, bishops, rooks, and queens "
                    "can all create devastating double attacks.</p>"
                    + fen_diagram(
                        "8/8/8/8/2r1b3/3P4/8/3K4",
                        "The d3-pawn forks the rook and bishop",
                        "d3,c4,e4",
                    )
                    + '<div class="highlight-box">'
                    "<b>Tip:</b> Always scan for fork opportunities, especially "
                    "with knights. Look for undefended pieces on the same "
                    "'knight circle'."
                    "</div>",
                    anchor="forks",
                ),
            ),
            Page(
                anchor="pins",
                html=wrap_page(
                    "<h1>Pins</h1>"
                    "<p>A <b>pin</b> occurs when a piece cannot move because "
                    "doing so would expose a more valuable piece (or the king) "
                    "behind it to attack.</p>"
                    "<h2>Absolute Pin</h2>"
                    "<p>If the piece behind is the <b>king</b>, the pinned piece "
                    "<b>cannot legally move</b> at all.</p>"
                    + fen_diagram(
                        "4k3/8/4n3/8/8/8/8/4R2K",
                        "The rook pins the knight to the king — it cannot move",
                        "e1,e6,e8",
                    )
                    + "<h2>Relative Pin</h2>"
                    "<p>If the piece behind is not the king, the pinned piece "
                    "<em>can</em> move — but moving it would lose material.</p>"
                    + fen_diagram(
                        "3kq3/8/4b3/8/8/8/8/4R2K",
                        "The bishop is pinned to the queen — it can move, but usually loses material",
                        "e1,e6,e8",
                    )
                    + '<div class="note">Bishops, rooks, and queens are the '
                    "only pieces that can create pins (line pieces).</div>",
                    anchor="pins",
                ),
            ),
            Page(
                anchor="skewers",
                html=wrap_page(
                    "<h1>Skewers</h1>"
                    "<p>A <b>skewer</b> is like a reversed pin. A piece attacks "
                    "a valuable piece that <em>must</em> move, revealing a second "
                    "piece behind it for capture.</p>"
                    + fen_diagram(
                        "8/8/8/8/8/r7/k7/R6K",
                        "The rook on a1 skewers the king on a2 and wins the rook on a3",
                        "a1,a2,a3",
                    )
                    + "<p>The black king on a2 must move, allowing Rxa3.</p>"
                    '<div class="highlight-box">'
                    "Skewers are especially effective along ranks, files, and "
                    "diagonals where the king and queen are aligned."
                    "</div>",
                    anchor="skewers",
                ),
            ),
            Page(
                anchor="discovered",
                html=wrap_page(
                    "<h1>Discovered Attacks</h1>"
                    "<p>A <b>discovered attack</b> occurs when moving one piece "
                    "reveals an attack from another piece behind it.</p>"
                    + fen_diagram(
                        "4k3/4p3/8/8/4N3/8/8/4R2K",
                        "If the knight moves away from e4, it reveals the rook's attack on e7",
                        "e4,e1,e7",
                    )
                    + "<h2>Discovered Check</h2>"
                    "<p>If the revealed attack is a <b>check</b>, it is called a "
                    "<b>discovered check</b>. The moving piece can go anywhere "
                    "— the opponent must deal with the check first.</p>"
                    "<h2>Double Check</h2>"
                    "<p>If <b>both</b> the moving piece and the uncovered piece "
                    "give check simultaneously, the king <b>must move</b> — "
                    "blocking or capturing cannot answer both checks.</p>"
                    + fen_diagram(
                        "4k3/8/4N3/8/8/8/8/4R2K",
                        "Nc7+ would be a double check: both knight and rook give check",
                        "e6,c7,e1,e8",
                    )
                    + '<div class="note">Double check is one of the most '
                    "powerful tactical motifs in chess.</div>",
                    anchor="discovered",
                ),
            ),
            Page(
                anchor="sacrifices",
                html=wrap_page(
                    "<h1>Sacrifices</h1>"
                    "<p>A <b>sacrifice</b> is a deliberate offer of material "
                    "to gain a positional advantage, initiate an attack, or "
                    "force checkmate.</p>"
                    "<h2>Types of Sacrifices</h2>"
                    "<ul>"
                    "<li><b>Tactical sacrifice</b> — material is regained by "
                    "force (with interest).</li>"
                    "<li><b>Positional sacrifice</b> — material is invested "
                    "for long-term compensation (activity, initiative).</li>"
                    "</ul>"
                    "<h2>Classic Example</h2>"
                    + fen_diagram(
                        "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R",
                        "Italian Game — White can sacrifice with Bxf7+!?",
                        "c4,f7",
                    )
                    + '<div class="highlight-box">'
                    "<b>Tip:</b> Before sacrificing, calculate! Ask yourself: "
                    "«What do I get in return? Can my opponent defend? Is there "
                    "a forced sequence?»"
                    "</div>"
                    '<div class="note">Many of the most beautiful games in '
                    "chess history include brilliant sacrifices. Study classics "
                    "to improve your tactical vision.</div>",
                    anchor="sacrifices",
                ),
            ),
        )
        return Chapter(chapter_id=self.chapter_id, title="Tactics", pages=pages)

    # ── Russian ──────────────────────────────────────────────────────

    def _build_ru(self) -> Chapter:
        pages = (
            Page(
                anchor="forks",
                html=wrap_page(
                    "<h1>Двойной удар (вилка)</h1>"
                    "<p><b>Вилка</b> — ход, при котором одна фигура "
                    "атакует <b>две или более</b> фигуры противника "
                    "одновременно.</p>"
                    "<h2>Коневая вилка</h2>"
                    "<p>Кони — лучшие «вилочники» благодаря L-образному "
                    "ходу.</p>"
                    + fen_diagram(
                        "8/2r1k3/8/3N4/8/8/8/4K3",
                        "Конь на d5 делает вилку королю e7 и ладье c7",
                        "d5,e7,c7",
                    )
                    + "<h2>Другие вилки</h2>"
                    "<p>Любая фигура может создать вилку — пешки, слоны, "
                    "ладьи, ферзь.</p>"
                    + fen_diagram(
                        "8/8/8/8/2r1b3/3P4/8/3K4",
                        "Пешка d3 атакует ладью и слона",
                        "d3,c4,e4",
                    )
                    + '<div class="highlight-box">'
                    "<b>Совет:</b> всегда ищите вилки, особенно конём. "
                    "Обращайте внимание на незащищённые фигуры.</div>",
                    anchor="forks",
                ),
            ),
            Page(
                anchor="pins",
                html=wrap_page(
                    "<h1>Связка</h1>"
                    "<p><b>Связка</b> — ситуация, когда фигура не может "
                    "двигаться, потому что за ней более ценная фигура "
                    "(или король).</p>"
                    "<h2>Абсолютная связка</h2>"
                    "<p>Если за фигурой стоит <b>король</b>, связанная "
                    "фигура <b>не может ходить</b> вообще.</p>"
                    + fen_diagram(
                        "4k3/8/4n3/8/8/8/8/4R2K",
                        "Ладья связывает коня с королём",
                        "e1,e6,e8",
                    )
                    + "<h2>Относительная связка</h2>"
                    "<p>Если за фигурой не король, она <em>может</em> "
                    "пойти — но это приведёт к материальным потерям.</p>"
                    + fen_diagram(
                        "3kq3/8/4b3/8/8/8/8/4R2K",
                        "Слон связан с ферзём — ходить можно, но не стоит",
                        "e1,e6,e8",
                    )
                    + '<div class="note">Связку могут создать только '
                    "линейные фигуры: слон, ладья, ферзь.</div>",
                    anchor="pins",
                ),
            ),
            Page(
                anchor="skewers",
                html=wrap_page(
                    "<h1>Сквозной удар</h1>"
                    "<p><b>Сквозной удар (линейный удар)</b> — обратная "
                    "связка. Ценная фигура <em>вынуждена</em> уйти, "
                    "открывая фигуру за ней для взятия.</p>"
                    + fen_diagram(
                        "8/8/8/8/8/r7/k7/R6K",
                        "Ладья на a1 наносит сквозной удар: король уходит, теряется ладья на a3",
                        "a1,a2,a3",
                    )
                    + '<div class="highlight-box">'
                    "Сквозные удары особенно эффективны по линиям, где "
                    "выстроились король и ферзь."
                    "</div>",
                    anchor="skewers",
                ),
            ),
            Page(
                anchor="discovered",
                html=wrap_page(
                    "<h1>Вскрытое нападение</h1>"
                    "<p><b>Вскрытое нападение</b> — ход одной фигурой "
                    "открывает линию атаки другой.</p>"
                    + fen_diagram(
                        "4k3/4p3/8/8/4N3/8/8/4R2K",
                        "Конь уходит с e4 — ладья сразу давит на e7",
                        "e4,e1,e7",
                    )
                    + "<h2>Вскрытый шах</h2>"
                    "<p>Если открывающаяся атака — <b>шах</b>, перемещённая "
                    "фигура может встать куда угодно.</p>"
                    "<h2>Двойной шах</h2>"
                    "<p>Если <b>обе</b> фигуры дают шах, король <b>обязан "
                    "уйти</b> — закрыться или взять обе фигуры невозможно.</p>"
                    + fen_diagram(
                        "4k3/8/4N3/8/8/8/8/4R2K",
                        "Кc7+ — двойной шах: и конь, и ладья",
                        "e6,c7,e1,e8",
                    )
                    + '<div class="note">Двойной шах — один из мощнейших '
                    "тактических приёмов.</div>",
                    anchor="discovered",
                ),
            ),
            Page(
                anchor="sacrifices",
                html=wrap_page(
                    "<h1>Жертва</h1>"
                    "<p><b>Жертва</b> — сознательная отдача материала "
                    "ради позиционного преимущества, атаки или мата.</p>"
                    "<h2>Виды жертв</h2>"
                    "<ul>"
                    "<li><b>Тактическая</b> — материал отыгрывается "
                    "конкретным расчётом.</li>"
                    "<li><b>Позиционная</b> — материал инвестируется "
                    "в долгосрочную компенсацию.</li>"
                    "</ul>"
                    "<h2>Классический пример</h2>"
                    + fen_diagram(
                        "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R",
                        "Итальянская партия — белые могут пожертвовать Сxf7+!?",
                        "c4,f7",
                    )
                    + '<div class="highlight-box">'
                    "<b>Совет:</b> перед жертвой считайте! Что я получу? "
                    "Может ли соперник защититься?"
                    "</div>",
                    anchor="sacrifices",
                ),
            ),
        )
        return Chapter(chapter_id=self.chapter_id, title="Тактика", pages=pages)
