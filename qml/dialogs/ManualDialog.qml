import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: root
    title: qsTr("Chess Manual")
    modal: false
    width: Math.min(680, Overlay.overlay.width * 0.92)
    height: Math.min(560, Overlay.overlay.height * 0.88)
    anchors.centerIn: Overlay.overlay

    property var chapters: [
        {
            title: qsTr("1. Introduction"),
            body: qsTr(
                "Chess is a two-player strategy board game played on an 8×8 grid of 64 squares. " +
                "Each player begins with 16 pieces: one king, one queen, two rooks, two bishops, " +
                "two knights, and eight pawns.\n\n" +
                "The goal is to checkmate the opponent's king — to attack the king so that it has " +
                "no legal escape. If a player has no legal move and their king is not in check, " +
                "the game is a draw by stalemate.\n\n" +
                "White always moves first. Players alternate moves for the rest of the game."
            )
        },
        {
            title: qsTr("2. The Pieces"),
            body: qsTr(
                "King (K): Moves one square in any direction. The king may never move into check.\n\n" +
                "Queen (Q): Combines the power of rook and bishop — any number of squares " +
                "along a rank, file, or diagonal.\n\n" +
                "Rook (R): Moves any number of squares along a rank or file.\n\n" +
                "Bishop (B): Moves any number of squares diagonally. Each bishop stays on " +
                "squares of one color.\n\n" +
                "Knight (N): Moves in an L-shape: two squares in one direction and one square " +
                "perpendicular. Knights may jump over other pieces.\n\n" +
                "Pawn (P): Moves forward one square (two from its starting rank). Captures " +
                "diagonally forward one square."
            )
        },
        {
            title: qsTr("3. Special Moves"),
            body: qsTr(
                "Castling: Once per game, the king moves two squares toward a rook, and the rook " +
                "jumps to the other side of the king. Castling is only legal if neither piece has " +
                "moved, the squares between them are empty, the king is not in check, and the king " +
                "does not pass through or land on an attacked square.\n\n" +
                "En passant: If a pawn advances two squares and could have been captured had it moved " +
                "one square, the opponent may capture it as if it moved one square.\n\n" +
                "Promotion: A pawn reaching the far rank must be promoted to a queen, rook, bishop, " +
                "or knight."
            )
        },
        {
            title: qsTr("4. Notation"),
            body: qsTr(
                "Algebraic notation records each move using piece letters and destination squares. " +
                "Files are labeled a–h from left to right for White; ranks are 1–8 from bottom to top.\n\n" +
                "Examples: e4 (pawn to e4), Nf3 (knight to f3), Bxc5 (bishop captures on c5), " +
                "O-O (kingside castling), e8=Q (promotion to queen).\n\n" +
                "A plus sign (+) means check; a hash (#) means checkmate. Move numbers show the " +
                "turn count: 1. e4 e5 means White's first move and Black's reply."
            )
        },
        {
            title: qsTr("5. Tactics"),
            body: qsTr(
                "Tactics are short combinations that win material or deliver mate.\n\n" +
                "Fork: One piece attacks two enemy pieces at once.\n\n" +
                "Pin: A piece cannot move without exposing a more valuable piece behind it.\n\n" +
                "Skewer: A valuable piece is attacked and must move, exposing a piece behind it.\n\n" +
                "Discovered attack: Moving one piece uncovers an attack from another.\n\n" +
                "Back-rank mate: The king is trapped on its home rank by its own pawns while enemy " +
                "rooks or queen deliver mate.\n\n" +
                "Look for checks, captures, and threats on every move."
            )
        },
        {
            title: qsTr("6. Openings"),
            body: qsTr(
                "The opening is the first phase of the game. General principles:\n\n" +
                "• Control the center with pawns and pieces.\n" +
                "• Develop knights and bishops toward the center.\n" +
                "• Castle early to safeguard the king.\n" +
                "• Do not move the same piece twice without reason.\n" +
                "• Connect your rooks and coordinate your pieces.\n\n" +
                "Popular openings include 1. e4 (King's Pawn), 1. d4 (Queen's Pawn), the Italian Game " +
                "(1. e4 e5 2. Nf3 Nc6 3. Bc4), and the Sicilian Defense (1. e4 c5)."
            )
        },
        {
            title: qsTr("7. Endgame"),
            body: qsTr(
                "The endgame begins when most pieces have been exchanged. Key ideas:\n\n" +
                "King activity: In the endgame the king becomes a fighting piece and should advance " +
                "toward the center.\n\n" +
                "Pawn promotion: Passed pawns (no enemy pawns blocking their path) are very powerful. " +
                "Support them with your king and pieces.\n\n" +
                "Opposition: Kings facing each other with one square between them — the side not to move " +
                "often must give way.\n\n" +
                "Basic checkmates to know: king and queen vs king, king and rook vs king. " +
                "Practice these until you can deliver mate within fifty moves."
            )
        }
    ]

    RowLayout {
        anchors.fill: parent
        spacing: 8

        ListView {
            id: chapterList
            Layout.preferredWidth: 180
            Layout.fillHeight: true
            clip: true
            model: root.chapters
            currentIndex: 0
            delegate: ItemDelegate {
                required property var modelData
                required property int index
                width: chapterList.width
                text: modelData.title
                highlighted: chapterList.currentIndex === index
                onClicked: chapterList.currentIndex = index
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            Column {
                width: parent.width
                spacing: 12
                padding: 12

                Label {
                    width: parent.width
                    text: root.chapters[chapterList.currentIndex].title
                    font.bold: true
                    font.pixelSize: 18
                    wrapMode: Text.WordWrap
                }

                Text {
                    width: parent.width
                    text: root.chapters[chapterList.currentIndex].body
                    wrapMode: Text.WordWrap
                    color: "#d4d4d4"
                    lineHeight: 1.35
                    font.pixelSize: 13
                }
            }
        }
    }
}
