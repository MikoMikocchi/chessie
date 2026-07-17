import QtQuick
import QtQuick.Controls
import Chessie 1.0

Button {
    id: root

    property color normalBg: Application.buttonBackground
    property color hoverBg: Application.buttonHover
    property color pressedBg: Application.buttonPressed
    property color dangerBg: Application.buttonDanger
    property bool danger: false

    flat: true
    padding: 8

    background: Rectangle {
        radius: 4
        color: {
            if (!root.enabled)
                return Application.buttonDisabled
            if (root.down)
                return root.danger ? "#5a1818" : root.pressedBg
            if (root.hovered)
                return root.danger ? "#7a2424" : root.hoverBg
            return root.danger ? root.dangerBg : root.normalBg
        }
        border.color: root.enabled ? "#555555" : "#3c3c3c"
        border.width: 1
    }

    contentItem: Text {
        text: root.text
        font.pixelSize: 13
        color: root.enabled ? Application.textPrimary : Application.textMuted
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
