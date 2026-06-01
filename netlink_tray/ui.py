from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter, QPainterPath, QPen, QBrush
from PyQt5.QtCore import QRectF, Qt, QTimer
from netlink_tray.core import check_port

def create_tunnel_icon(is_active):
    # Generates a simplified, thick, high-contrast SSH tunnel icon
    # Optimized for maximum readability in small system trays
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    if is_active:
        color_remote = QColor(0, 191, 255)     # Bright sky blue (Remote Host)
        color_local = QColor(0, 255, 128)      # Bright neon green (Local Host)
        color_arrow = QColor(0, 255, 128)      # Green data flow
        arrow_style = Qt.SolidLine
    else:
        color_remote = QColor(120, 120, 120)   # Dull gray
        color_local = QColor(120, 120, 120)    # Dull gray
        color_arrow = QColor(230, 70, 70)      # Vibrant red (Disconnected)
        arrow_style = Qt.DashLine

    # 1. Draw Local Host (Left): Bold server tower
    rect_local = QRectF(4, 6, 6, 20)
    painter.setPen(QPen(color_local, 2.5))
    painter.setBrush(QBrush(QColor(25, 25, 25)))
    painter.drawRoundedRect(rect_local, 1.5, 1.5)
    
    # 2. Draw Remote Host (Right): Bold server tower
    rect_remote = QRectF(22, 6, 6, 20)
    painter.setPen(QPen(color_remote, 2.5))
    painter.setBrush(QBrush(QColor(25, 25, 25)))
    painter.drawRoundedRect(rect_remote, 1.5, 1.5)
    
    # 3. Draw Tunnel/Data Flow (Arrow from Right to Left)
    pen_arrow = QPen(color_arrow, 3.5, arrow_style, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen_arrow)
    
    # Arrow body
    painter.drawLine(21, 16, 11, 16)
    
    # Arrow head pointing left (Local)
    path_head = QPainterPath()
    path_head.moveTo(15, 12)
    path_head.lineTo(11, 16)
    path_head.lineTo(15, 20)
    painter.drawPath(path_head)
    
    # 4. Draw internal status indicator lights on servers
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(color_local))
    painter.drawEllipse(QRectF(6, 10, 2, 2))
    painter.setBrush(QBrush(color_remote))
    painter.drawEllipse(QRectF(24, 10, 2, 2))
    
    painter.end()
    return QIcon(pixmap)

class NetlinkTray(QSystemTrayIcon):
    def __init__(self, port, polling_interval_ms, parent=None):
        super().__init__(parent)
        self.port = port
        
        self.icon_active = create_tunnel_icon(True)
        self.icon_inactive = create_tunnel_icon(False)
        self.current_state = None
        
        self.setToolTip(f"Netlink Tray - Port Monitor {self.port}")
        
        # Right-click menu
        menu = QMenu()
        exit_action = QAction("Close Monitor", menu)
        exit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(exit_action)
        self.setContextMenu(menu)
        
        # Periodic polling timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.periodic_check)
        self.timer.start(polling_interval_ms)
        
        # Initial check
        self.periodic_check()

    def periodic_check(self):
        is_active = check_port(self.port)
        self.update_status(is_active)

    def update_status(self, is_active):
        if self.current_state == is_active:
            return
            
        self.current_state = is_active
        if is_active:
            self.setIcon(self.icon_active)
        else:
            self.setIcon(self.icon_inactive)
