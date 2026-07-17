import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Chessie 1.0

Dialog {
    id: root
    title: qsTr("Settings")
    modal: true
    width: Math.min(560, Overlay.overlay.width * 0.9)
    anchors.centerIn: Overlay.overlay
    standardButtons: Dialog.Ok | Dialog.Cancel
    padding: 16

    background: Rectangle {
        color: Application.panelBackground
        radius: 6
        border.color: Application.borderColor
    }

    header: Label {
        text: root.title
        color: Application.textPrimary
        font.bold: true
        font.pixelSize: 15
        padding: 12
    }

    onAccepted: applySettings()

    function applySettings() {
        SettingsStore.language = languageCombo.currentText
        SettingsStore.boardTheme = themeCombo.currentText
        SettingsStore.showCoordinates = coordsCheck.checked
        SettingsStore.showLegalMoves = legalCheck.checked
        SettingsStore.animateMoves = animCheck.checked
        SettingsStore.useFigurineNotation = figurineCheck.checked
        SettingsStore.soundEnabled = soundCheck.checked
        SettingsStore.soundVolume = volumeSlider.value
        SettingsStore.engineDepth = engineDepthSpin.value
        SettingsStore.engineTimeMs = engineTimeSpin.value
        SettingsStore.analysisDepth = analysisDepthSpin.value
        SettingsStore.analysisTimeMs = analysisTimeSpin.value
    }

    Component.onCompleted: loadSettings()

    function loadSettings() {
        languageCombo.currentIndex = Math.max(0, languageCombo.find(SettingsStore.language))
        themeCombo.currentIndex = Math.max(0, themeCombo.find(SettingsStore.boardTheme))
        coordsCheck.checked = SettingsStore.showCoordinates
        legalCheck.checked = SettingsStore.showLegalMoves
        animCheck.checked = SettingsStore.animateMoves
        figurineCheck.checked = SettingsStore.useFigurineNotation
        soundCheck.checked = SettingsStore.soundEnabled
        volumeSlider.value = SettingsStore.soundVolume
        engineDepthSpin.value = SettingsStore.engineDepth
        engineTimeSpin.value = SettingsStore.engineTimeMs
        analysisDepthSpin.value = SettingsStore.analysisDepth
        analysisTimeSpin.value = SettingsStore.analysisTimeMs
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        TabBar {
            id: tabs
            Layout.fillWidth: true
            TabButton { text: qsTr("General") }
            TabButton { text: qsTr("Board") }
            TabButton { text: qsTr("Sound") }
            TabButton { text: qsTr("Engine") }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabs.currentIndex

            ColumnLayout {
                spacing: 8
                Label { text: qsTr("Language"); font.bold: true }
                ComboBox {
                    id: languageCombo
                    Layout.fillWidth: true
                    model: ["English", "Russian"]
                }
            }

            ColumnLayout {
                spacing: 8
                Label { text: qsTr("Board"); font.bold: true }
                Label { text: qsTr("Theme") }
                ComboBox {
                    id: themeCombo
                    Layout.fillWidth: true
                    model: ["Classic", "Blue", "Green", "Walnut", "Slate"]
                }
                CheckBox { id: coordsCheck; text: qsTr("Coordinates") }
                CheckBox { id: legalCheck; text: qsTr("Legal move hints") }
                CheckBox { id: animCheck; text: qsTr("Animate moves") }
                CheckBox { id: figurineCheck; text: qsTr("Figurine notation") }
            }

            ColumnLayout {
                spacing: 8
                Label { text: qsTr("Sound"); font.bold: true }
                CheckBox { id: soundCheck; text: qsTr("Enabled") }
                Label { text: qsTr("Volume") }
                Slider {
                    id: volumeSlider
                    Layout.fillWidth: true
                    from: 0
                    to: 100
                    stepSize: 1
                }
            }

            ColumnLayout {
                spacing: 8
                Label { text: qsTr("Engine"); font.bold: true }
                RowLayout {
                    Label { text: qsTr("Search depth") }
                    SpinBox { id: engineDepthSpin; from: 1; to: 20 }
                }
                RowLayout {
                    Label { text: qsTr("Move time (ms)") }
                    SpinBox { id: engineTimeSpin; from: 100; to: 60000; stepSize: 100 }
                }
                RowLayout {
                    Label { text: qsTr("Analysis depth") }
                    SpinBox { id: analysisDepthSpin; from: 1; to: 20 }
                }
                RowLayout {
                    Label { text: qsTr("Analysis time (ms)") }
                    SpinBox { id: analysisTimeSpin; from: 50; to: 10000; stepSize: 50 }
                }
            }
        }
    }
}
