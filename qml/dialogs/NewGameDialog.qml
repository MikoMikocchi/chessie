import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Chessie 1.0

Dialog {
    id: root
    title: qsTr("New Game")
    modal: true
    anchors.centerIn: Overlay.overlay
    standardButtons: Dialog.Ok | Dialog.Cancel
    padding: 16

    background: Rectangle {
        color: Application.panelBackground
        radius: 6
        border.color: Application.borderColor
    }

    property var timePresets: [
        qsTr("Bullet 1+0"),
        qsTr("Blitz 3+2"),
        qsTr("Rapid 10+0"),
        qsTr("Rapid 15+10"),
        qsTr("Classical 30+0"),
        qsTr("Unlimited")
    ]

    onAccepted: {
        GameControllerModel.startNewGame(
            opponentCombo.currentIndex === 0 ? "human" : "ai",
            colorGroup.checkedButton === blackRadio ? 1 : 0,
            timeCombo.currentIndex
        )
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 12

        Label { text: qsTr("Opponent") }
        ComboBox {
            id: opponentCombo
            Layout.fillWidth: true
            model: [qsTr("Human"), qsTr("Engine")]
            currentIndex: 1
        }

        Label { text: qsTr("Play as") }
        RowLayout {
            ButtonGroup { id: colorGroup }
            RadioButton {
                id: whiteRadio
                text: qsTr("White")
                checked: true
                ButtonGroup.group: colorGroup
            }
            RadioButton {
                id: blackRadio
                text: qsTr("Black")
                ButtonGroup.group: colorGroup
            }
        }

        Label { text: qsTr("Time control") }
        ComboBox {
            id: timeCombo
            Layout.fillWidth: true
            model: root.timePresets
            currentIndex: 2
        }
    }
}
