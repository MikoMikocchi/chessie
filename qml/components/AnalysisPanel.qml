import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Chessie 1.0

ColumnLayout {
    id: root
    spacing: 6

    Label {
        Layout.fillWidth: true
        text: qsTr("Analysis")
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
        color: Application.textPrimary
    }

    AccuracyRow {
        Layout.fillWidth: true
        label: "♔"
        value: GameControllerModel.whiteAccuracy
        barColor: "#f0f0f0"
    }

    AccuracyRow {
        Layout.fillWidth: true
        label: "♚"
        value: GameControllerModel.blackAccuracy
        barColor: "#646464"
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: judgmentGrid.implicitHeight + 12
        radius: 6
        color: "#2a2a2a"

        GridLayout {
            id: judgmentGrid
            anchors.fill: parent
            anchors.margins: 6
            columns: 2

            JudgmentColumn {
                Layout.fillWidth: true
                judgments: GameControllerModel.whiteJudgments
            }

            Rectangle {
                Layout.fillHeight: true
                width: 1
                color: "#444444"
            }

            JudgmentColumn {
                Layout.fillWidth: true
                judgments: GameControllerModel.blackJudgments
            }
        }
    }

    Rectangle {
        Layout.fillWidth: true
        visible: GameControllerModel.analysisMoveVisible
        radius: 6
        color: "#2a2a2a"
        implicitHeight: moveColumn.implicitHeight + 16

        ColumnLayout {
            id: moveColumn
            anchors.fill: parent
            anchors.margins: 8
            spacing: 4

            Label {
                Layout.fillWidth: true
                text: GameControllerModel.analysisMoveTitle
                font.bold: true
                wrapMode: Text.WordWrap
                color: "#d0d0d0"
            }
            Label {
                Layout.fillWidth: true
                text: GameControllerModel.analysisMovePlayed
                wrapMode: Text.WordWrap
                color: "#b0b0b0"
            }
            Label {
                Layout.fillWidth: true
                text: GameControllerModel.analysisMoveBest
                wrapMode: Text.WordWrap
                color: "#9bc700"
            }
            Label {
                Layout.fillWidth: true
                text: GameControllerModel.analysisMoveEval
                color: "#888888"
            }
        }
    }

    component AccuracyRow: RowLayout {
        property string label: ""
        property real value: 0
        property color barColor: "#cccccc"

        Label {
            text: label
            font.bold: true
            color: "#c0c0c0"
            Layout.preferredWidth: 24
        }
        ProgressBar {
            Layout.fillWidth: true
            from: 0
            to: 100
            value: parent.value
            background: Rectangle {
                radius: 3
                color: "#1e1e1e"
                border.color: "#444444"
            }
            contentItem: Item {
                Rectangle {
                    width: parent.parent.visualPosition * parent.parent.width
                    height: parent.parent.height
                    radius: 3
                    color: parent.parent.parent.barColor
                }
            }
        }
        Label {
            text: value.toFixed(1) + "%"
            font.bold: true
            color: Application.textPrimary
            Layout.preferredWidth: 48
            horizontalAlignment: Text.AlignRight
        }
    }

    component JudgmentColumn: ColumnLayout {
        property var judgments: ({})

        Repeater {
            model: [
                { key: "best", label: qsTr("Best"), color: "#9bc700" },
                { key: "good", label: qsTr("Good"), color: "#88bb44" },
                { key: "inaccuracy", label: qsTr("Inaccuracy"), color: "#cccc44" },
                { key: "mistake", label: qsTr("Mistake"), color: "#ff8800" },
                { key: "blunder", label: qsTr("Blunder"), color: "#ff4444" }
            ]
            delegate: RowLayout {
                required property var modelData
                Layout.fillWidth: true
                Label {
                    text: modelData.label
                    color: "#b0b0b0"
                    font.pixelSize: 11
                    Layout.fillWidth: true
                }
                Label {
                    text: judgments[modelData.key] || 0
                    font.bold: true
                    color: modelData.color
                    Layout.preferredWidth: 24
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }
}
