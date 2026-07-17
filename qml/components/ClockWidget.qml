import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Chessie 1.0

RowLayout {
    id: root
    spacing: 8

    function formatTime(seconds) {
        if (seconds < 0)
            return "∞"
        const s = Math.max(0, seconds)
        const mins = Math.floor(s / 60)
        const secs = Math.floor(s % 60)
        const tenths = Math.floor((s * 10) % 10)
        if (mins >= 10)
            return mins + ":" + secs.toString().padStart(2, "0")
        return mins + ":" + secs.toString().padStart(2, "0") + "." + tenths
    }

    function clockBg(isWhite) {
        const active = GameControllerModel.activeClockColor === (isWhite ? 0 : 1)
        const seconds = isWhite ? GameControllerModel.whiteClockSeconds
                                : GameControllerModel.blackClockSeconds
        if (!active)
            return "#2b2b2b"
        if (seconds >= 0 && seconds < 30)
            return "#8b2020"
        return "#3a7d44"
    }

    function clockFg(isWhite) {
        const active = GameControllerModel.activeClockColor === (isWhite ? 0 : 1)
        return active ? "#ffffff" : "#aaaaaa"
    }

    component ClockFace: Item {
        required property bool isWhite
        Layout.fillWidth: true
        Layout.preferredHeight: 56
        implicitWidth: 110
        implicitHeight: 56

        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            text: isWhite ? qsTr("White") : qsTr("Black")
            color: "#aaaaaa"
            font.pixelSize: 11
        }

        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            width: 110
            height: 36
            radius: 4
            color: clockBg(isWhite)

            Text {
                anchors.centerIn: parent
                width: parent.width - 16
                horizontalAlignment: Text.AlignHCenter
                font.family: "Menlo, Consolas, monospace"
                font.pixelSize: 22
                font.bold: true
                color: clockFg(isWhite)
                text: formatTime(isWhite ? GameControllerModel.whiteClockSeconds
                                         : GameControllerModel.blackClockSeconds)
            }
        }
    }

    ClockFace { isWhite: true }
    ClockFace { isWhite: false }
}
