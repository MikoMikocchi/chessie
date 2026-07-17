import QtQuick
import QtQuick.Controls
import Chessie 1.0
import "."

Item {
    id: root

    readonly property var pieces: GameControllerModel.boardPieces
    readonly property int selectedSquare: GameControllerModel.selectedSquare
    readonly property var legalTargets: GameControllerModel.legalTargetSquares
    readonly property int lastFrom: GameControllerModel.lastMoveFrom
    readonly property int lastTo: GameControllerModel.lastMoveTo
    readonly property int checkSquare: GameControllerModel.checkSquare

    function visualToSquare(visualIndex, flipped) {
        const fileVis = visualIndex % 8
        const rankVis = Math.floor(visualIndex / 8)
        if (!flipped) {
            const rank = 7 - rankVis
            return rank * 8 + fileVis
        }
        const file = 7 - fileVis
        return rankVis * 8 + file
    }

    function pieceCodeFor(sq) {
        for (let i = 0; i < pieces.length; ++i) {
            const entry = pieces[i]
            if (entry.square === sq)
                return entry.code
        }
        return ""
    }

    Grid {
        id: boardGrid
        anchors.centerIn: parent
        width: Math.min(parent.width, parent.height)
        height: width
        columns: 8
        rows: 8
        spacing: 0

        property bool flipped: GameControllerModel.flipped
        property bool interactive: GameControllerModel.interactive

        Repeater {
            model: 64
            delegate: Square {
                required property int index
                width: boardGrid.width / 8
                height: boardGrid.height / 8
                squareIndex: index
                flipped: boardGrid.flipped
                showCoordinates: SettingsStore.showCoordinates
                displaySquare: root.visualToSquare(index, boardGrid.flipped)
                isLight: {
                    const file = displaySquare % 8
                    const rank = Math.floor(displaySquare / 8)
                    return (file + rank) % 2 === 1
                }
                isSelected: displaySquare === root.selectedSquare
                isLegalTarget: root.legalTargets.indexOf(displaySquare) >= 0
                isLastMove: displaySquare === root.lastFrom || displaySquare === root.lastTo
                isCheck: displaySquare === root.checkSquare
                pieceCode: root.pieceCodeFor(displaySquare)

                onClicked: {
                    if (!boardGrid.interactive)
                        return
                    GameControllerModel.selectSquare(displaySquare)
                }
                onDropRequested: function(fromSquare, toSquare) {
                    if (!boardGrid.interactive)
                        return
                    GameControllerModel.tryMove(fromSquare, toSquare)
                }
            }
        }
    }
}
