import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import Chessie 1.0
import "components"
import "dialogs"

ApplicationWindow {
    id: root
    width: 1100
    height: 750
    minimumWidth: 900
    minimumHeight: 640
    visible: true
    title: qsTr("Chessie")
    color: Application.windowBackground

    palette {
        window: Application.windowBackground
        windowText: Application.textPrimary
        base: Application.panelBackground
        text: Application.textPrimary
        button: Application.buttonBackground
        buttonText: Application.textPrimary
        highlight: Application.buttonPressed
        highlightedText: "#f0f6ff"
    }

    Component.onCompleted: {
        Application.bindSettings(SettingsStore)
        GameControllerModel.bindSettings(SettingsStore)
        GameControllerModel.startDefaultGame()
    }

    Connections {
        target: GameControllerModel
        function onPromotionRequired() {
            if (GameControllerModel.promotionPending)
                promotionDialog.open()
        }
        function onGameOverDialogRequested(message) {
            confirmDialog.title = qsTr("Game Over")
            confirmDialog.message = message
            confirmDialog.action = ""
            confirmDialog.open()
        }
        function onConfirmDialogRequested(title, message, acceptAction) {
            confirmDialog.title = title
            confirmDialog.message = message
            confirmDialog.acceptText = qsTr("Yes")
            confirmDialog.rejectText = qsTr("No")
            confirmDialog.action = acceptAction
            confirmDialog.open()
        }
        function onDrawOfferReceived() {
            confirmDialog.title = qsTr("Draw Offer")
            confirmDialog.message = qsTr("Your opponent offers a draw. Accept?")
            confirmDialog.acceptText = qsTr("Accept")
            confirmDialog.rejectText = qsTr("Decline")
            confirmDialog.action = "draw"
            confirmDialog.open()
        }
        function onAnalysisReportReady(summary) {
            analysisDialog.summary = summary
            analysisDialog.open()
        }
    }

    menuBar: MenuBar {
        background: Rectangle { color: Application.windowBackground }
        delegate: MenuBarItem {
            palette.highlight: Application.buttonHover
            palette.highlightedText: Application.textPrimary
            contentItem: Text {
                text: parent.text
                color: Application.textPrimary
                font.pixelSize: 13
                leftPadding: 8
                rightPadding: 8
                verticalAlignment: Text.AlignVCenter
            }
            background: Rectangle {
                color: parent.highlighted ? Application.buttonHover : "transparent"
            }
        }

        Menu {
            title: qsTr("Game")
            Action {
                text: qsTr("New Game")
                shortcut: "Ctrl+N"
                onTriggered: newGameDialog.open()
            }
            Action {
                text: qsTr("Open PGN")
                shortcut: "Ctrl+O"
                onTriggered: openPgnDialog.open()
            }
            Action {
                text: qsTr("Save PGN")
                shortcut: "Ctrl+S"
                onTriggered: savePgnDialog.open()
            }
            Action {
                text: qsTr("Analyze")
                shortcut: "Ctrl+Shift+A"
                onTriggered: GameControllerModel.startAnalysis()
            }
            MenuSeparator {}
            Action {
                text: qsTr("Flip")
                shortcut: "F"
                onTriggered: GameControllerModel.flipBoard()
            }
            MenuSeparator {}
            Action {
                text: qsTr("Quit")
                shortcut: "Ctrl+Q"
                onTriggered: Qt.quit()
            }
        }
        Menu {
            title: qsTr("Settings")
            Action {
                text: qsTr("Settings…")
                shortcut: "Ctrl+,"
                onTriggered: settingsDialog.open()
            }
        }
        Menu {
            title: qsTr("Help")
            Action {
                text: qsTr("Manual")
                shortcut: "F1"
                onTriggered: manualDialog.open()
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 8

        EvalBar {
            Layout.fillHeight: true
            evalCp: GameControllerModel.evalCp
            evalMate: GameControllerModel.evalMate
        }

        ChessBoard {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredWidth: 560
            Layout.minimumWidth: 320
            Layout.minimumHeight: 320
        }

        Rectangle {
            Layout.preferredWidth: 280
            Layout.fillHeight: true
            color: Application.panelBackground
            radius: 4
            border.color: Application.borderColor
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 8

                ClockWidget {
                    Layout.fillWidth: true
                    visible: !GameControllerModel.analysisMode
                }

                EvalGraph {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 100
                    visible: GameControllerModel.analysisMode
                    evalData: GameControllerModel.evalGraphData
                    markerColors: GameControllerModel.evalGraphColors
                    activePly: GameControllerModel.historyViewPly
                    onPlySelected: function(ply) {
                        GameControllerModel.selectPly(ply)
                        GameControllerModel.showAnalysisPly(ply)
                    }
                }

                AnalysisPanel {
                    Layout.fillWidth: true
                    visible: GameControllerModel.analysisMode
                }

                MoveList {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }

                ControlPanel {
                    Layout.fillWidth: true
                    visible: !GameControllerModel.analysisMode
                }

                ChessButton {
                    Layout.fillWidth: true
                    visible: GameControllerModel.analysisMode
                    text: qsTr("Exit Analysis")
                    onClicked: GameControllerModel.exitAnalysis()
                }
            }
        }
    }

    footer: Rectangle {
        implicitHeight: 28
        color: Application.statusBarBackground
        border.color: Application.borderColor
        border.width: 1

        Label {
            anchors.fill: parent
            anchors.leftMargin: 10
            verticalAlignment: Text.AlignVCenter
            text: GameControllerModel.statusText
            color: Application.textPrimary
            font.pixelSize: 13
        }
    }

    NewGameDialog { id: newGameDialog }
    PromotionDialog { id: promotionDialog }
    SettingsDialog { id: settingsDialog }
    AnalysisDialog { id: analysisDialog }
    ManualDialog { id: manualDialog }
    ConfirmDialog { id: confirmDialog }

    FileDialog {
        id: openPgnDialog
        title: qsTr("Open PGN")
        nameFilters: [qsTr("PGN files (*.pgn)")]
        fileMode: FileDialog.OpenFile
        onAccepted: GameControllerModel.openPgn(selectedFile)
    }

    FileDialog {
        id: savePgnDialog
        title: qsTr("Save PGN")
        nameFilters: [qsTr("PGN files (*.pgn)")]
        fileMode: FileDialog.SaveFile
        onAccepted: GameControllerModel.savePgn(selectedFile)
    }
}
