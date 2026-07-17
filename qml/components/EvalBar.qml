import QtQuick
import QtQuick.Controls

Item {
    id: root
    width: 28
    implicitHeight: 200

    property real evalCp: 0
    property int evalMate: 0

    readonly property real ratio: {
        if (evalMate !== 0)
            return evalMate > 0 ? 0.95 : 0.05
        const clamped = Math.max(-1000, Math.min(1000, evalCp))
        return (clamped + 1000) / 2000
    }

    Rectangle {
        anchors.fill: parent
        radius: 3
        color: "#323232"
    }

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: parent.height * ratio
        radius: 3
        color: "#f0f0f0"
    }

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.bottomMargin: parent.height * ratio - 1
        height: 2
        color: "#646464"
    }

    Label {
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width
        horizontalAlignment: Text.AlignHCenter
        font.pixelSize: 9
        color: "#787878"
        text: {
            if (evalMate !== 0)
                return "M" + Math.abs(evalMate)
            return (evalCp / 100).toFixed(1)
        }
    }
}
