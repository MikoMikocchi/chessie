import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Chessie 1.0

Dialog {
    id: root
    title: qsTr("Promote Pawn")
    modal: true
    anchors.centerIn: Overlay.overlay

    onOpened: promotionColor = GameControllerModel.promotionColor

    property int promotionColor: 0

    ColumnLayout {
        anchors.fill: parent
        spacing: 12

        Label {
            Layout.fillWidth: true
            text: qsTr("Choose promotion piece:")
            horizontalAlignment: Text.AlignHCenter
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 8

            Repeater {
                model: [
                    { type: 5, code: promotionColor === 0 ? "wQ" : "bQ", label: qsTr("Queen") },
                    { type: 4, code: promotionColor === 0 ? "wR" : "bR", label: qsTr("Rook") },
                    { type: 3, code: promotionColor === 0 ? "wB" : "bB", label: qsTr("Bishop") },
                    { type: 2, code: promotionColor === 0 ? "wN" : "bN", label: qsTr("Knight") }
                ]
                delegate: ToolButton {
                    required property var modelData
                    implicitWidth: 68
                    implicitHeight: 68
                    ToolTip.text: modelData.label
                    ToolTip.visible: hovered

                    background: Rectangle {
                        radius: 6
                        color: parent.down || parent.hovered ? "#3c3c3c" : "#2b2b2b"
                        border.color: "#555555"
                    }

                    contentItem: Image {
                        source: "image://svg/" + modelData.code
                        fillMode: Image.PreserveAspectFit
                        smooth: true
                    }

                    onClicked: {
                        GameControllerModel.completePromotion(modelData.type)
                        root.close()
                    }
                }
            }
        }

        DialogButtonBox {
            Layout.fillWidth: true
            standardButtons: DialogButtonBox.Cancel
            onRejected: {
                GameControllerModel.cancelPromotion()
                root.close()
            }
        }
    }
}
