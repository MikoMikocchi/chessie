import QtQuick
import QtQuick.Controls
import Chessie 1.0

ScrollView {
    id: root
    clip: true

    contentWidth: availableWidth

    Column {
        width: root.availableWidth
        spacing: 2
        padding: 4

        Label {
            width: parent.width
            text: qsTr("Moves")
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            color: Application.textPrimary
        }

        Repeater {
            model: GameControllerModel.moves
            delegate: Row {
                required property int index
                required property int moveNumber
                required property string whiteSan
                required property string blackSan
                required property int whitePly
                required property int blackPly
                required property string whiteNag
                required property string blackNag
                required property string whiteNagColor
                required property string blackNagColor
                required property int activePly

                width: parent.width
                spacing: 6
                padding: 2

                Label {
                    width: 28
                    horizontalAlignment: Text.AlignRight
                    verticalAlignment: Text.AlignVCenter
                    text: moveNumber + "."
                    color: Application.textPrimary
                }

                MoveButton {
                    width: (parent.width - 40) / 2
                    label: formatSan(whiteSan, true)
                    nag: whiteNag
                    nagColor: whiteNagColor
                    active: activePly === whitePly
                    onActivated: GameControllerModel.selectPly(whitePly)
                }

                MoveButton {
                    width: (parent.width - 40) / 2
                    visible: blackSan !== ""
                    label: formatSan(blackSan, false)
                    nag: blackNag
                    nagColor: blackNagColor
                    active: activePly === blackPly
                    onActivated: GameControllerModel.selectPly(blackPly)
                }

                function formatSan(san, isWhite) {
                    if (!SettingsStore.useFigurineNotation || san === "")
                        return san
                    const table = isWhite
                        ? { K: "♔", Q: "♕", R: "♖", B: "♗", N: "♘" }
                        : { K: "♚", Q: "♛", R: "♜", B: "♝", N: "♞" }
                    let out = san
                    if (out.length > 0 && table[out[0]])
                        out = table[out[0]] + out.slice(1)
                    const eq = out.indexOf("=")
                    if (eq >= 0) {
                        const promo = out.charAt(eq + 1)
                        if (table[promo])
                            out = out.slice(0, eq + 1) + table[promo] + out.slice(eq + 2)
                    }
                    return out
                }
            }
        }
    }

    component MoveButton: ToolButton {
        property string label: ""
        property string nag: ""
        property string nagColor: "#cccccc"
        property bool active: false

        signal activated()

        text: label + (nag ? " " + nag : "")
        onClicked: activated()
        flat: !active
        background: Rectangle {
            radius: 4
            color: active ? "#264f78" : (parent.down || parent.hovered ? "#3c3c3c" : "transparent")
            border.color: active ? "#3b79b7" : "transparent"
        }
        contentItem: Text {
            text: parent.text
            color: active ? "#f0f6ff" : Application.textPrimary
            font: parent.font
            horizontalAlignment: Text.AlignLeft
            verticalAlignment: Text.AlignVCenter
            leftPadding: 8
        }
    }
}
