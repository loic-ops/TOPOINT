import ipaddress
import socket

from fastapi import Request, HTTPException

from app.config import settings
from app.utils.ip import get_client_ip


def _is_in_allowed_subnets(ip_str: str) -> bool:
    """Vérifie si l'IP est dans l'un des sous-réseaux autorisés."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False

    # Si aucun sous-réseau configuré, auto-détecter le subnet local
    subnets = settings.ALLOWED_SUBNETS
    if not subnets:
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            network = ipaddress.ip_network(f"{local_ip}/24", strict=False)
            return ip in network
        except Exception:
            return False

    for subnet in subnets:
        try:
            if ip in ipaddress.ip_network(subnet, strict=False):
                return True
        except ValueError:
            continue
    return False


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
