import ipaddress
import socket
import struct
import threading

from fastapi import Request, HTTPException

from app.config import settings
from app.utils.ip import get_client_ip

# Plage /24 du réseau bureaux auto-détectée (cache)
_office_network = None
_office_lock = threading.Lock()

# Préfixes d'interfaces à ignorer (interne Docker / loopback / link-local)
_EXCLUDED_PREFIXES = ("127.", "172.17.", "172.18.", "172.19.", "172.2",
                      "172.30.", "172.31.", "169.254.", "::1", "fe80:")


def _detect_office_network() -> ipaddress.IPv4Network | None:
    """
    Détecte le subnet LAN bureaux du serveur.
    Méthode portable : un socket UDP "connecté" à une IP externe révèle
    l'IP source (interface LAN principale) sans émettre aucun paquet.
    Exclut loopback, link-local et réseaux internes Docker.
    """
    candidates = []

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.settimeout(0)
            s.connect(("8.8.8.8", 80))
            candidates.append(s.getsockname()[0])
        finally:
            s.close()
    except OSError:
        pass

    # Fallback : énumération des interfaces (Linux/conteneur)
    try:
        import fcntl
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            for _, name in socket.if_nameindex():
                try:
                    packed = struct.unpack("256s", fcntl.ioctl(
                        s.fileno(), 0x8915, struct.pack("256s", name[:15].encode())
                    ))[20:24]
                    candidates.append(socket.inet_ntoa(packed))
                except OSError:
                    continue
        finally:
            s.close()
    except Exception:
        pass

    # Dernier recours : résolution du hostname
    try:
        candidates.append(socket.gethostbyname(socket.gethostname()))
    except OSError:
        pass

    # Préférence aux IP privées IPv4 hors réseaux internes Docker/loopback
    for ip in candidates:
        if ip.startswith(_EXCLUDED_PREFIXES):
            continue
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            continue
        if addr.is_private and addr.version == 4:
            return ipaddress.ip_network(f"{ip}/24", strict=False)
    return None


def get_office_networks() -> list[str]:
    """Subnets de référence : ALLOWED_SUBNETS si défini, sinon auto-détection."""
    if settings.ALLOWED_SUBNETS:
        return list(settings.ALLOWED_SUBNETS)
    global _office_network
    with _office_lock:
        if _office_network is None:
            _office_network = _detect_office_network()
    return [str(_office_network)] if _office_network else []


def is_in_office(ip_str: str) -> bool | None:
    """
    L'IP appartient-elle au réseau bureaux ?
    Retourne None si aucune plage de référence n'est déterminable
    (ex: conteneur Docker sans ALLOWED_SUBNETS) → "indéterminé".
    Simple indicateur, ne bloque jamais le pointage.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return None

    subnets = get_office_networks()
    if not subnets:
        return None

    for subnet in subnets:
        try:
            if ip in ipaddress.ip_network(subnet, strict=False):
                return True
        except ValueError:
            continue
    return False


def _is_in_allowed_subnets(ip_str: str) -> bool:
    """Compat : vérifie si l'IP est dans l'un des sous-réseaux autorisés."""
    return is_in_office(ip_str) is True


def verify_local_network(request: Request):
    """
    Vérifie que la requête provient du réseau local autorisé.
    Désactivé automatiquement quand DEPLOY_MODE=demo.
    """
    # En mode demo (cloud), on ne vérifie pas le réseau
    if settings.DEPLOY_MODE == "demo":
        return

    client_ip = get_client_ip(request)
    if not _is_in_allowed_subnets(client_ip):
        raise HTTPException(
            status_code=403,
            detail="Accès réservé au réseau local autorisé",
        )
