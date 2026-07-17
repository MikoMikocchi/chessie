import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Chessie 1.0

Dialog {
    id: root
    title: qsTr("Confirm")
    modal: true
    width: Math.min(420, Overlay.overlay.width * 0.85)
    anchors.centerIn: Overlay.overlay

    property string message: ""
    property string acceptText: qsTr("Yes")
    property string rejectText: qsTr("No")
    property string action: ""

    standardButtons: rejectText === "" ? Dialog.Ok : Dialog.Yes | Dialog.No

    onAccepted: {
        if (action === "resign")
            GameControllerModel.confirmResign()
        else if (action === "draw")
            GameControllerModel.acceptDraw()
    }
    onRejected: {
        if (action === "draw")
            GameControllerModel.declineDraw()
    }

    Label {
        width: parent.width
        wrapMode: Text.WordWrap
        text: message
        padding: 8
    }
}
