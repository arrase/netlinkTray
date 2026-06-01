import sys
import socket
import struct
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter, QPainterPath, QPen, QBrush
from PyQt5.QtCore import QRectF, Qt, QTimer

# --- CONFIGURACIÓN ---
PUERTO = "2222"
# ---------------------

def create_tunnel_icon(is_active):
    # Genera un icono de túnel SSH simplificado, grueso y de alto contraste
    # Optimizado para máxima legibilidad en system trays pequeños
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    if is_active:
        color_remote = QColor(0, 191, 255)     # Azul cielo brillante (Host Remoto)
        color_local = QColor(0, 255, 128)      # Verde neón brillante (Host Local)
        color_arrow = QColor(0, 255, 128)      # Flujo de datos verde
        arrow_style = Qt.SolidLine
    else:
        color_remote = QColor(120, 120, 120)   # Gris apagado
        color_local = QColor(120, 120, 120)    # Gris apagado
        color_arrow = QColor(230, 70, 70)      # Rojo vibrante (Desconectado)
        arrow_style = Qt.DashLine

    # 1. Dibujar Host Local (Izquierda): Torre de servidor bold
    rect_local = QRectF(4, 6, 6, 20)
    painter.setPen(QPen(color_local, 2.5))
    painter.setBrush(QBrush(QColor(25, 25, 25)))
    painter.drawRoundedRect(rect_local, 1.5, 1.5)
    
    # 2. Dibujar Host Remoto (Derecha): Torre de servidor bold
    rect_remote = QRectF(22, 6, 6, 20)
    painter.setPen(QPen(color_remote, 2.5))
    painter.setBrush(QBrush(QColor(25, 25, 25)))
    painter.drawRoundedRect(rect_remote, 1.5, 1.5)
    
    # 3. Dibujar Túnel/Flujo de Datos (Flecha de Derecha a Izquierda)
    pen_arrow = QPen(color_arrow, 3.5, arrow_style, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen_arrow)
    
    # Cuerpo de la flecha
    painter.drawLine(21, 16, 11, 16)
    
    # Cabeza de la flecha apuntando a la izquierda (Local)
    path_head = QPainterPath()
    path_head.moveTo(15, 12)
    path_head.lineTo(11, 16)
    path_head.lineTo(15, 20)
    painter.drawPath(path_head)
    
    # 4. Dibujar luces indicadoras de estado internas en los servidores
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(color_local))
    painter.drawEllipse(QRectF(6, 10, 2, 2))
    painter.setBrush(QBrush(color_remote))
    painter.drawEllipse(QRectF(24, 10, 2, 2))
    
    painter.end()
    return QIcon(pixmap)

# --- Constantes Netlink INET_DIAG ---
NETLINK_SOCK_DIAG = 4
SOCK_DIAG_BY_FAMILY = 20
NLM_F_REQUEST = 0x01
NLM_F_DUMP = 0x300
NLMSG_DONE = 3
NLMSG_ERROR = 2
NLMSG_HDR_SIZE = 16
TCPF_ALL = 0xFFF  # Bitmask: todos los estados TCP (ESTABLISHED..CLOSING)


def _build_diag_request(family):
    """Construye un mensaje Netlink INET_DIAG para volcar todos los sockets TCP."""
    # inet_diag_req_v2: family(u8), protocol(u8), ext(u8), pad(u8), states(u32)
    req = struct.pack("=BBBBI", family, socket.IPPROTO_TCP, 0, 0, TCPF_ALL)
    # inet_diag_sockid (48 bytes): ceros excepto cookie = INET_DIAG_NOCOOKIE (~0)
    req += b'\0' * 40 + b'\xff' * 8
    # Cabecera Netlink
    msg_len = NLMSG_HDR_SIZE + len(req)
    return struct.pack("=IHHII", msg_len, SOCK_DIAG_BY_FAMILY,
                       NLM_F_REQUEST | NLM_F_DUMP, 0, 0) + req


def _scan_diag_response(nl_sock, port):
    """Lee respuestas Netlink buscando si algún socket usa el puerto especificado."""
    while True:
        data = nl_sock.recv(65536)
        offset = 0
        while offset < len(data):
            nlmsg_len, nlmsg_type = struct.unpack_from("=IH", data, offset)
            if nlmsg_len == 0:
                return False
            if nlmsg_type in (NLMSG_DONE, NLMSG_ERROR):
                return False
            if nlmsg_type == SOCK_DIAG_BY_FAMILY:
                # inet_diag_msg: family(1)+state(1)+timer(1)+retrans(1), luego sockid
                # sockid empieza con sport(__be16) y dport(__be16) en network byte order
                sport, dport = struct.unpack_from(
                    "!HH", data, offset + NLMSG_HDR_SIZE + 4
                )
                if sport == port or dport == port:
                    return True
            offset += (nlmsg_len + 3) & ~3


def check_port(port):
    """Comprueba si el puerto está en uso consultando al kernel vía Netlink INET_DIAG."""
    port_int = int(port)
    try:
        with socket.socket(socket.AF_NETLINK, socket.SOCK_DGRAM,
                           NETLINK_SOCK_DIAG) as nl:
            nl.bind((0, 0))
            for family in (socket.AF_INET, socket.AF_INET6):
                nl.send(_build_diag_request(family))
                if _scan_diag_response(nl, port_int):
                    return True
            return False
    except Exception:
        return False

class NetlinkTray(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.icon_active = create_tunnel_icon(True)
        self.icon_inactive = create_tunnel_icon(False)
        self.current_state = None  # Almacena el estado para evitar redibujados
        
        self.setToolTip(f"Netlink Tray - Monitor de Puerto {PUERTO}")
        
        # Menú del clic derecho
        menu = QMenu()
        exit_action = QAction("Cerrar Monitor", menu)
        exit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(exit_action)
        self.setContextMenu(menu)
        
        # Temporizador de sondeo periódico (simple y elegante en lugar de un QThread)
        self.timer = QTimer()
        self.timer.timeout.connect(self.periodic_check)
        self.timer.start(1500) # Comprobación cada 1.5 segundos
        
        # Comprobación inicial
        self.periodic_check()

    def periodic_check(self):
        is_active = check_port(PUERTO)
        self.update_status(is_active)

    def update_status(self, is_active):
        if self.current_state == is_active:
            return # Evitar actualizar el icono si el estado es el mismo
            
        self.current_state = is_active
        if is_active:
            self.setIcon(self.icon_active)
        else:
            self.setIcon(self.icon_inactive)

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    monitor = NetlinkTray()
    monitor.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
