import socket
import struct

# --- Netlink INET_DIAG Constants ---
NETLINK_SOCK_DIAG = 4
SOCK_DIAG_BY_FAMILY = 20
NLM_F_REQUEST = 0x01
NLM_F_DUMP = 0x300
NLMSG_DONE = 3
NLMSG_ERROR = 2
NLMSG_HDR_SIZE = 16
TCPF_ALL = 0xFFF  # Bitmask: all TCP states (ESTABLISHED..CLOSING)

def _build_diag_request(family):
    """Builds a Netlink INET_DIAG message to dump all TCP sockets."""
    # inet_diag_req_v2: family(u8), protocol(u8), ext(u8), pad(u8), states(u32)
    req = struct.pack("=BBBBI", family, socket.IPPROTO_TCP, 0, 0, TCPF_ALL)
    # inet_diag_sockid (48 bytes): zeros except cookie = INET_DIAG_NOCOOKIE (~0)
    req += b'\0' * 40 + b'\xff' * 8
    # Netlink Header
    msg_len = NLMSG_HDR_SIZE + len(req)
    return struct.pack("=IHHII", msg_len, SOCK_DIAG_BY_FAMILY,
                       NLM_F_REQUEST | NLM_F_DUMP, 0, 0) + req

def _scan_diag_response(nl_sock, port):
    """Reads Netlink responses checking if any socket uses the specified port."""
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
                # inet_diag_msg: family(1)+state(1)+timer(1)+retrans(1), then sockid
                # sockid starts with sport(__be16) and dport(__be16) in network byte order
                sport, dport = struct.unpack_from(
                    "!HH", data, offset + NLMSG_HDR_SIZE + 4
                )
                if sport == port or dport == port:
                    return True
            offset += (nlmsg_len + 3) & ~3

def check_port(port):
    """Checks if the port is in use by querying the kernel via Netlink INET_DIAG."""
    port_int = int(port)
    try:
        with socket.socket(socket.AF_NETLINK, socket.SOCK_DGRAM, NETLINK_SOCK_DIAG) as nl:
            nl.bind((0, 0))
            for family in (socket.AF_INET, socket.AF_INET6):
                nl.send(_build_diag_request(family))
                if _scan_diag_response(nl, port_int):
                    return True
            return False
    except Exception:
        return False
