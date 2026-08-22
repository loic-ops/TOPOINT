from fastapi import Request

from app.config import settings


def get_client_ip(request: Request) -> str:
    """
    Extrait l'IP réelle du client.

    - Mode "local" (déploiement LAN) : l'app est servie directement par uvicorn
      sans reverse-proxy de confiance → on utilise l'IP source TCP
      (request.client.host), non forgeable par le client.
      Les headers X-Forwarded-For / X-Real-IP sont ignorés car n'importe
      quel téléphone pourrait les falsifier.

    - Mode "demo" (cloud derrière un load balancer) : l'IP est dans
      X-Forwarded-For, sinon c'est celle du proxy.
    """
    if settings.DEPLOY_MODE == "demo":
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

    # IP source TCP réelle de la connexion (LAN local ou fallback cloud)
    if request.client:
        return request.client.host

    return "unknown"
