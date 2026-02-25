"""BoardView — QGraphicsView wrapper for the board scene."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QResizeEvent
from PyQt6.QtWidgets import QGraphicsView, QSizePolicy

from chessie.core.move import Move
from chessie.ui.board.board_scene import BoardScene


class BoardView(QGraphicsView):
    """Displays the board scene, handles scaling to fit the widget.

    Signals:
        move_made(Move): Bubbled up from BoardScene.
    """

    move_made = pyqtSignal(Move)

    def __init__(self, parent=None) -> None:
        self._scene = BoardScene()
        super().__init__(self._scene, parent)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setRenderHint(self.renderHints())
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 320)

        # Bubble scene signal
        self._scene.move_made.connect(self.move_made.emit)

    @property
    def board_scene(self) -> BoardScene:
        return self._scene

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
