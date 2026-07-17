import QtQuick
import QtQuick.Controls
import Chessie 1.0
import "."

Rectangle {
    id: root

    required property int squareIndex
    required property bool isLight
    required property int displaySquare
    required property bool flipped
    required property bool showCoordinates
    required property bool isSelected
    required property bool isLegalTarget
    required property bool isLastMove
    required property bool isCheck
    required property string pieceCode

    signal clicked()
    signal dropRequested(int fromSquare, int toSquare)

    color: {
        if (isCheck)
            return Application.highlightCheck
        if (isSelected)
            return Application.highlightFrom
        if (isLastMove)
            return Application.lastMoveTo
        return isLight ? Application.lightSquare : Application.darkSquare
    }

    Rectangle {
        visible: isLegalTarget && SettingsStore.showLegalMoves
        anchors.centerIn: parent
        width: Math.min(parent.width, parent.height) * 0.28
        height: width
        radius: width / 2
        color: Application.highlightTo
    }

    Text {
        visible: showCoordinates && shouldShowCoord
        anchors.left: showFile ? parent.left : undefined
        anchors.bottom: showFile ? parent.bottom : undefined
        anchors.right: showRank ? parent.right : undefined
        anchors.top: showRank ? parent.top : undefined
        anchors.margins: 3
        text: coordText
        font.pixelSize: Math.max(10, parent.width * 0.14)
        color: isLight ? Application.coordLight : Application.coordDark
        opacity: 0.85

        property bool showFile: displaySquare % 8 === 0
        property bool showRank: displaySquare < 8
        property bool shouldShowCoord: showFile || showRank
        property string coordText: {
            let parts = []
            if (showFile) {
                const rank = Math.floor(displaySquare / 8) + 1
                parts.push(String(rank))
            }
            if (showRank) {
                const file = String.fromCharCode(97 + (displaySquare % 8))
                parts.push(file)
            }
            return parts.join("")
        }
    }

    Piece {
        id: pieceItem
        anchors.fill: parent
        anchors.margins: parent.width * 0.06
        visible: pieceCode !== ""
        pieceCode: root.pieceCode
        squareIndex: displaySquare
        pieceEnabled: GameControllerModel.interactive

        onDragFinished: function(fromSquare, toSquare) {
            root.dropRequested(fromSquare, toSquare)
        }
        onClicked: root.clicked()
    }

    MouseArea {
        anchors.fill: parent
        enabled: pieceCode === "" && GameControllerModel.interactive
        onClicked: root.clicked()
    }
}
