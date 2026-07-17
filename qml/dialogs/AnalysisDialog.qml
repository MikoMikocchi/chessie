import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: root
    title: qsTr("Analysis Report")
    modal: true
    anchors.centerIn: Overlay.overlay
    standardButtons: Dialog.Ok

    property string summary: ""

    Label {
        width: Math.min(420, Overlay.overlay.width * 0.85)
        wrapMode: Text.WordWrap
        text: summary
        padding: 8
    }
}
