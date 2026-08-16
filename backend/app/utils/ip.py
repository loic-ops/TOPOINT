from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    Extrait l'IP réelle du client.
    En local : request.client.host fonctionne.
    En cloud (Render, Heroku, etc.) : l'IP est dans X-Forwarded-For
    car le reverse proxy interpose l'adresse du load balancer.
    """
    # X-Forwarded-For : premier enregistrement = IP réelle du client
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    # X-Real-IP : alternative utilisée par certains proxy
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback : IP directe (fonctionne en local)
    if request.client:
        return request.client.host

    return "unknown"
