import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Chessie 1.0
import "."

ColumnLayout {
    id: root
    spacing: 6

    RowLayout {
        Layout.fillWidth: true
        spacing: 6

        ChessButton {
            Layout.fillWidth: true
            text: qsTr("Undo")
            enabled: GameControllerModel.gameActive
            onClicked: GameControllerModel.undo()
        }
        ChessButton {
            Layout.fillWidth: true
            text: qsTr("Resign")
            enabled: GameControllerModel.gameActive
            danger: true
            onClicked: GameControllerModel.resign()
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 6

        ChessButton {
            Layout.fillWidth: true
            text: qsTr("Draw")
            enabled: GameControllerModel.gameActive
            onClicked: GameControllerModel.offerDraw()
        }
        ChessButton {
            Layout.fillWidth: true
            text: qsTr("Flip")
            onClicked: GameControllerModel.flipBoard()
        }
    }
}
