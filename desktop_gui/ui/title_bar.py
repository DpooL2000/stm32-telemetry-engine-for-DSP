from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QPen

class CustomTitleBar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(35)
        self.start_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title_label = QLabel("GX TELEMETRY ENGINE")
        title_label.setObjectName("mainTitle")
        layout.addWidget(title_label)
        layout.addStretch()

        min_btn = QPushButton("—")
        min_btn.setObjectName("titleBtn")
        min_btn.clicked.connect(self.parent.showMinimized)
        layout.addWidget(min_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self.parent.close)
        layout.addWidget(close_btn)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#1a1a24"))

        pen = QPen(QColor("#ffaa00"))
        pen.setWidth(2)
        painter.setPen(pen)

        w = self.width()
        h = self.height()
        c = 15  

        painter.drawLine(QPoint(0, c), QPoint(c, 0))
        painter.drawLine(QPoint(c, 0), QPoint(w, 0))
        painter.drawLine(QPoint(0, h), QPoint(w, h))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.start_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        if self.start_pos is not None:
            delta = event.globalPosition().toPoint() - self.start_pos
            self.parent.move(self.parent.pos() + delta)
            self.start_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event):
        self.start_pos = None
