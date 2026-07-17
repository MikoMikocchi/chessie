import QtQuick
import QtQuick.Controls

Canvas {
    id: root
    height: 100
    implicitHeight: 100

    property var evalData: []
    property var markerColors: []
    property int activePly: -1

    signal plySelected(int ply)

    onEvalDataChanged: requestPaint()
    onMarkerColorsChanged: requestPaint()
    onActivePlyChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    readonly property real marginLeft: 28
    readonly property real marginRight: 6
    readonly property real marginTop: 6
    readonly property real marginBottom: 14
    readonly property real maxEval: 600

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: function(mouse) {
            if (evalData.length < 2)
                return
            const chartW = root.width - marginLeft - marginRight
            const ratio = (mouse.x - marginLeft) / chartW
            const ply = Math.round(ratio * (evalData.length - 1))
            root.plySelected(Math.max(0, Math.min(evalData.length - 1, ply)))
        }
    }

    onPaint: {
        const ctx = getContext("2d")
        ctx.clearRect(0, 0, width, height)
        ctx.fillStyle = "#262626"
        ctx.fillRect(0, 0, width, height)

        const chartLeft = marginLeft
        const chartTop = marginTop
        const chartW = width - marginLeft - marginRight
        const chartH = height - marginTop - marginBottom

        if (evalData.length < 2) {
            ctx.fillStyle = "#646464"
            ctx.font = "10px sans-serif"
            ctx.textAlign = "center"
            ctx.fillText("—", width / 2, height / 2)
            return
        }

        function evalToY(ev) {
            const clamped = Math.max(-maxEval, Math.min(maxEval, ev))
            const ratio = 0.5 - clamped / (2 * maxEval)
            return chartTop + ratio * chartH
        }

        function plyToX(ply) {
            const n = Math.max(1, evalData.length - 1)
            return chartLeft + (ply / n) * chartW
        }

        const centerY = evalToY(0)
        ctx.strokeStyle = "#5a5a5a"
        ctx.setLineDash([4, 4])
        ctx.beginPath()
        ctx.moveTo(chartLeft, centerY)
        ctx.lineTo(chartLeft + chartW, centerY)
        ctx.stroke()
        ctx.setLineDash([])

        ctx.beginPath()
        for (let i = 0; i < evalData.length; ++i) {
            const x = plyToX(i)
            const y = evalToY(evalData[i])
            if (i === 0)
                ctx.moveTo(x, y)
            else
                ctx.lineTo(x, y)
        }
        ctx.strokeStyle = "#b4c8dc"
        ctx.lineWidth = 1.5
        ctx.stroke()

        for (let i = 0; i < markerColors.length && i < evalData.length; ++i) {
            if (!markerColors[i])
                continue
            ctx.fillStyle = markerColors[i]
            ctx.beginPath()
            ctx.arc(plyToX(i), evalToY(evalData[i]), 3.5, 0, Math.PI * 2)
            ctx.fill()
        }

        if (activePly >= 0 && activePly < evalData.length) {
            const ax = plyToX(activePly)
            ctx.strokeStyle = "rgba(100,160,255,0.8)"
            ctx.lineWidth = 1.5
            ctx.beginPath()
            ctx.moveTo(ax, chartTop)
            ctx.lineTo(ax, chartTop + chartH)
            ctx.stroke()
        }
    }
}
