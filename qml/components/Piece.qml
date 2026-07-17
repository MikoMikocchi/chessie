import QtQuick
import QtQuick.Controls
import Chessie 1.0

Item {
    id: root

    property bool pieceEnabled: true
    property string pieceCode: ""
    property int squareIndex: -1
    property bool dragging: false
    property real pressX: 0
    property real pressY: 0

    signal clicked()
    signal dragFinished(int fromSquare, int toSquare)

    Image {
        id: pieceImage
        anchors.fill: parent
        visible: !dragging
        source: pieceCode ? "image://svg/" + pieceCode : ""
        fillMode: Image.PreserveAspectFit
        smooth: true
        antialiasing: true
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        enabled: root.pieceEnabled && pieceCode !== ""
        drag.target: dragLayer
        drag.threshold: 8

        onPressed: function(mouse) {
            pressX = mouse.x
            pressY = mouse.y
            dragging = false
        }
        onClicked: function(mouse) {
            if (!dragging)
                root.clicked()
        }
        onReleased: function(mouse) {
            if (!dragging) {
                root.clicked()
                return
            }
            dragging = false
            dragLayer.x = 0
            dragLayer.y = 0
            const board = root.parent.parent
            if (!board)
                return
            const global = mapToItem(board, mouse.x, mouse.y)
            const cellW = board.width / 8
            const cellH = board.height / 8
            const fileVis = Math.floor(global.x / cellW)
            const rankVis = Math.floor(global.y / cellH)
            const visualIndex = rankVis * 8 + fileVis
            const flipped = GameControllerModel.flipped
            const fileVisClamped = Math.max(0, Math.min(7, fileVis))
            const rankVisClamped = Math.max(0, Math.min(7, rankVis))
            const vis = rankVisClamped * 8 + fileVisClamped
            let target = vis
            if (!flipped)
                target = (7 - rankVisClamped) * 8 + fileVisClamped
            else
                target = rankVisClamped * 8 + (7 - fileVisClamped)
            root.dragFinished(squareIndex, target)
        }
        onPositionChanged: function(mouse) {
            if (pressed && (Math.abs(mouse.x - pressX) > 8 || Math.abs(mouse.y - pressY) > 8))
                dragging = true
        }
    }

    Item {
        id: dragLayer
        width: root.width
        height: root.height
        x: 0
        y: 0
        z: dragging ? 100 : 0
        visible: dragging

        Image {
            anchors.fill: parent
            source: pieceImage.source
            fillMode: Image.PreserveAspectFit
            smooth: true
        }
    }
}
