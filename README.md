# Pointage  — Prototype empreinte digitale (WebAuthn)

## 1. Installer et lancer en local

```bash
pip install -r requirements.txt
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Va sur `http://localhost:8000` sur ton PC : ça marche déjà en HTTPS-équivalent
car `localhost` est considéré comme "sécurisé" par le navigateur.

## 2. Tester avec ton deuxième téléphone (comme capteur d'empreinte)

Le navigateur du téléphone doit accéder au serveur en **HTTPS** (sauf si tu
restes sur `localhost`, ce qui n'est pas possible depuis un autre appareil).
La solution la plus rapide : **ngrok**.

```bash
# Installer ngrok (une fois) : https://ngrok.com/download
ngrok http 8000
```

Ngrok te donne une URL du style `https://xxxx-xx-xx.ngrok-free.app`.

⚠️ Étape importante : ouvre `app.py` et modifie ces deux lignes en haut du
fichier avec ton URL ngrok exacte :

```python
RP_ID = "xxxx-xx-xx.ngrok-free.app"          # sans https:// et sans slash final
ORIGIN = "https://xxxx-xx-xx.ngrok-free.app" # avec https://
```

Relance le serveur (`Ctrl+C` puis relance `uvicorn`), puis ouvre l'URL ngrok
depuis le navigateur de ton **deuxième téléphone**.

## 3. Utilisation

1. Onglet "Enregistrer une empreinte" → tape le nom de l'employé →
   "Enregistrer mon empreinte" → le téléphone demande l'empreinte
   (capteur physique du téléphone) → une seule fois par personne.
2. Onglet "Pointer" → tape le nom → choisis Arrivée / Départ / Début pause /
   Fin pause → empreinte demandée à nouveau → horodatage enregistré.
3. La liste "Derniers pointages" en bas se met à jour automatiquement.

## Limites de ce prototype (à savoir avant de le montrer à l'équipe)

- Chaque **appareil-capteur** enregistre une empreinte par nom. Si 10
  employés utilisent le même téléphone comme borne de pointage, il faudra
  que chacun enregistre son empreinte une fois sur CE téléphone précis
  (normal avec WebAuthn : l'empreinte biométrique ne quitte jamais l'appareil).
- Les challenges WebAuthn sont stockés en mémoire (dict Python) — à
  remplacer par Redis ou la DB si tu passes en prod avec plusieurs workers.
- Pas d'authentification admin sur `/pointages` — à protéger avant tout
  déploiement réel.
- Base de données SQLite simple (`pointage.db`), suffisante pour un test
  mais à migrer vers MySQL si tu veux le brancher sur ton infra Likmed/HDL.

## Prochaine étape logique

Si le test valide l'approche, on peut :
- ajouter une page "admin" avec export CSV/Excel des pointages du mois
- calculer automatiquement heures travaillées / retards / pauses dépassées
- migrer vers MySQL et déployer sur le réseau local de HDL (comme
  ScholaTogo), avec une borne = un téléphone/tablette fixé à l'entrée
