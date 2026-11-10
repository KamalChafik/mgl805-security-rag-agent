
# MGL805 — Laboratoire de cybersécurité avec RAG et OWASP

Environnement de laboratoire reproductible permettant d'analyser des rapports de sécurité OWASP ZAP avec une intelligence artificielle locale et de consulter la documentation OWASP Top 10 à l'aide d'une recherche vectorielle (RAG).

Le projet déploie six services Docker :

- Open WebUI — Interface utilisateur et orchestration RAG
- ChromaDB — Base de données vectorielle
- Security Agent — API FastAPI d'analyse des rapports ZAP
- OWASP ZAP — Analyse de sécurité des applications Web
- DVWA — Application Web volontairement vulnérable
- MariaDB — Base de données de DVWA

Ollama fonctionne sur une machine externe disposant d'un GPU NVIDIA.

> **Sécurité :** ce laboratoire doit être utilisé uniquement sur des systèmes pour lesquels vous possédez une autorisation explicite. DVWA est intentionnellement vulnérable et ne doit pas être exposé sur Internet.

## 1. Architecture

```text
                  UTILISATEUR
                      |
                Navigateur Web
                      |
          +-----------+-----------+
          |           |           |
      Open WebUI     ZAP         DVWA
          |           |           |
          |           +---------->|
          |                       |
          |                    MariaDB
          |
    +-----+-------------------+
    |                         |
  Ollama                 ChromaDB
  (externe)              (Docker)
    |                         |
    | Embeddings              | Vecteurs
    +-------------------------+
    |
  LLM Qwen
    |
  OWASP Report Bridge
    |
  Security Agent (FastAPI)
    |
  Rapports JSON ZAP
```

### Fonctionnement du RAG

1. Open WebUI importe les documents OWASP.
2. Open WebUI découpe les documents en fragments.
3. Ollama génère les embeddings avec `qwen3-embedding:0.6b`.
4. ChromaDB conserve les vecteurs et les métadonnées.
5. Lors d'une recherche, Ollama génère l'embedding de la question.
6. ChromaDB retourne les fragments les plus pertinents.
7. Le modèle `qwen3.5:9b` produit une réponse à partir du contexte récupéré.

**ChromaDB ne génère pas les embeddings.** Leur génération est effectuée par Ollama et orchestrée par Open WebUI.

## 2. Accès aux services

Les URLs suivantes utilisent l'adresse IP de notre VM de laboratoire `media` : `192.168.2.17`.

| Service | Adresse |
|---|---|
| Open WebUI | http://192.168.2.17:3000 |
| DVWA | http://192.168.2.17:4280 |
| OWASP ZAP | http://192.168.2.17:8080/zap |
| ChromaDB | `http://chromadb:8000` (interne) |
| FastAPI | `http://security-agent:8000` (interne) |
| MariaDB | `db:3306` (interne) |

Remplacer `192.168.2.17` par l'adresse IP de votre VM.

Les URLs du navigateur doivent utiliser l'adresse IP de la VM et non `localhost`, sauf si vous utilisez explicitement un tunnel SSH.

**Important :** pour accéder à ZAP sur le port `8080`, le fichier `.env` doit contenir `ZAP_GUI_PORT=8080`. Le projet utilise `8088` par défaut dans certaines versions de `.env.example`.

## 3. Prérequis

Configuration recommandée :

| Ressource | Configuration |
|---|---|
| Système | Ubuntu Server 24.04 LTS |
| CPU | 4 vCPU |
| Mémoire | 8 Go minimum |
| Disque | 60 Go |
| Docker | Docker Engine et Compose v2 |
| Python | Python 3 |
| Ollama | Serveur externe accessible sur le réseau |

Les modèles requis sur Ollama sont :

- `qwen3.5:9b` pour le raisonnement et l'analyse.
- `qwen3-embedding:0.6b` pour les embeddings.

Vérifier les outils :

```bash
docker --version
docker compose version
python3 --version
git --version
```

## 4. Installation

### 4.1 Cloner le dépôt

```bash
git clone <URL_DU_DEPOT_GITHUB>
cd mgl805-security-rag-agent
```

### 4.2 Créer le fichier d'environnement

```bash
test -f .env || cp .env.example .env
nano .env
```

Configuration pour notre VM:

```dotenv
# OLLAMA
OLLAMA_URL=http://192.168.2.29:11434
EMBEDDING_MODEL=qwen3-embedding:0.6b
LLM_MODEL=qwen3.5:9b

# RESEAU
BIND_IP=192.168.2.17

# PORTS
WEBUI_PORT=3000
DVWA_PORT=4280
ZAP_GUI_PORT=8080

# SECRETS
# Générés automatiquement par start.sh au premier démarrage
WEBUI_SECRET_KEY=
DB_PASSWORD=
DB_ROOT_PASSWORD=

# OPEN WEBUI
# Configurés après la première connexion
KNOWLEDGE_ID=
OPENWEBUI_API_KEY=

# IMAGES
OPENWEBUI_IMAGE=ghcr.io/open-webui/open-webui:main
CHROMA_IMAGE=chromadb/chroma:1.5.3
ZAP_IMAGE=ghcr.io/zaproxy/zaproxy:stable
DVWA_IMAGE=ghcr.io/digininja/dvwa:latest
```

Les adresses IP sont propres à notre installation et doivent être adaptées à l'environnement cible.

Les tags `main`, `stable` et `latest` ne garantissent pas des versions identiques dans le temps. Pour un déploiement reproductible, privilégier des versions ou des digests vérifiés.

### 4.3 Vérifier Ollama

Depuis la VM :

```bash
curl --connect-timeout 5 \
  http://192.168.2.29:11434/api/tags
```

`Remplacez par l'IP de votre machine avec Ollama`
La réponse doit être `HTTP 200` et contenir les modèles requis.

Tester également avec le script du dépôt :

```bash
python3 scripts/check_ollama.py
```

Si la connexion échoue, vérifier :

- L'adresse IP actuelle du serveur Ollama.
- La variable `OLLAMA_HOST` sur la machine externe.
- Le pare-feu Windows ou Linux.
- La connectivité réseau entre la VM et le serveur.

### 4.4 Démarrer les conteneurs

```bash
chmod +x start.sh stop.sh scripts/*.sh

./start.sh --check-only
./start.sh
```

Le script initialise les répertoires persistants, génère les secrets manquants et démarre le projet Docker Compose.

Vérifier :

```bash
docker compose ps
```

Les conteneurs attendus sont :

```text
mgl805-open-webui
mgl805-chromadb
mgl805-security-agent
mgl805-zap
mgl805-dvwa
mgl805-dvwa-db
```

## 5. Vérification des ports

Vérifier les redirections Docker :

```bash
docker port mgl805-open-webui
docker port mgl805-dvwa
docker port mgl805-zap
```

Avec notre configuration, les redirections attendues sont :

```text
Open WebUI : 192.168.2.17:3000 -> 8080/tcp
DVWA       : 192.168.2.17:4280 -> 80/tcp
ZAP        : 192.168.2.17:8080 -> 8080/tcp
```

Tester les interfaces depuis la VM :

```bash
curl -I http://192.168.2.17:3000/
curl -I http://192.168.2.17:4280/
curl -I http://192.168.2.17:8080/zap
```

Une réponse HTTP confirme l'accessibilité du service. Des redirections HTTP peuvent être normales.

### Réseaux Docker

Dans la configuration corrigée, les services DVWA et ZAP utilisent également un réseau bridge `access` pour permettre la publication des ports.

Les réseaux du laboratoire restent séparés :

- `backend` : Open WebUI, ChromaDB et FastAPI.
- `lab` : communication entre l'agent, ZAP et DVWA.
- `dbnet` : communication entre DVWA et MariaDB.
- `access` : publication des interfaces DVWA et ZAP sur l'hôte.

MariaDB, FastAPI et ChromaDB ne nécessitent pas de ports publiés sur la VM.

**Attention :** les ports liés à l'IP de la VM peuvent être accessibles aux autres machines du LAN. Utiliser un réseau de laboratoire isolé ou des restrictions de pare-feu.

## 6. Configuration initiale de DVWA

Accéder à :

http://192.168.2.17:4280

1. Se connecter à DVWA avec les identifiants de démonstration.
2. Accéder à la page **Setup DVWA**.
3. Cliquer sur **Create / Reset Database**.
4. Vérifier que les pages DVWA fonctionnent.

La cible utilisée à l'intérieur du réseau Docker est :

```text
http://dvwa/
```

Il n'est pas nécessaire d'utiliser l'IP de la VM pour les communications entre conteneurs Docker.

## 7. Configuration initiale d'OWASP ZAP

Accéder à :

http://192.168.2.17:8080/zap

ZAP est lancé avec l'interface Webswing.

Depuis ZAP, utiliser la cible :

```text
http://dvwa/
```

Pour produire les rapports qui seront analysés par l'agent, exporter les résultats au format JSON dans :

```text
/zap/wrk/reports/
```

Ce répertoire correspond au dossier suivant sur la VM :

```text
./data/reports/
```

FastAPI dispose d'un accès en lecture seule à ces rapports.

L'API/proxy ZAP interne sur le port `8090` n'est pas exposée sur l'hôte dans cette version du projet.

## 8. Configuration initiale d'Open WebUI

Accéder à :

http://192.168.2.17:3000

### 8.1 Créer le compte administrateur

Lors de la première connexion, créer le compte administrateur Open WebUI.

### 8.2 Configurer Ollama

Dans les paramètres des connexions Open WebUI, vérifier que le serveur Ollama utilise :

```text
http://192.168.2.29:11434
```

Le modèle `qwen3.5:9b` doit être disponible.

Tester depuis le conteneur Open WebUI :

```bash
docker compose exec -T open-webui python -c \
'import os,urllib.request; u=os.environ["OLLAMA_BASE_URL"].rstrip("/")+"/api/tags"; print(urllib.request.urlopen(u,timeout=10).status)'
```

Résultat attendu :

```text
200
```

### 8.3 Activer les clés API — obligatoire

**L'utilisation des clés API doit être activée dans Open WebUI avant de pouvoir en créer une.**

Dans Open WebUI :

1. Se connecter en tant qu'administrateur.
2. Accéder à **Admin Panel → Settings → Authentication**.
3. Activer l'option **API Keys**.
4. Enregistrer les modifications.
5. Vérifier que les restrictions d'endpoints n'empêchent pas les appels nécessaires à l'importation.
6. Ouvrir **Settings → Account → Secrets**.
7. Créer une nouvelle clé API.
8. Copier la clé dans le fichier `.env`.

Exemple :

```dotenv
OPENWEBUI_API_KEY=sk-VOTRE_CLE_API
```

Ne pas ajouter `Bearer` dans cette valeur : les scripts Python ajoutent l'en-tête automatiquement.

Protéger le fichier :

```bash
chmod 600 .env
```

Ne jamais publier `.env`, les clés API ou les mots de passe dans le dépôt GitHub.

### 8.4 Dépannage des clés API

Si l'importation retourne :

```text
401 Unauthorized
```

Vérifier :

- L'activation globale de **API Keys**.
- La validité de la clé.
- La correspondance entre la clé et l'instance Open WebUI actuelle.
- La présence de `OPENWEBUI_API_KEY` dans `.env`.

Si l'API retourne `403 Forbidden`, vérifier les permissions du compte et les éventuelles restrictions d'endpoints.

## 9. Créer la base de connaissances OWASP

Dans Open WebUI :

1. Ouvrir **Workspace → Knowledge**.
2. Créer une collection nommée **OWASP Security Knowledge**.
3. Copier son identifiant UUID.
4. Ajouter l'identifiant dans `.env`.

Exemple :

```dotenv
KNOWLEDGE_ID=UUID_DE_LA_COLLECTION
```

L'identifiant est propre à chaque installation. Ne pas réutiliser celui de l'ancienne VM.

Pour transmettre `OWASP_COLLECTION_ID` au conteneur après modification de `.env` :

```bash
docker compose up -d --no-deps --force-recreate open-webui
```

### 9.1 Installer les outils Python

```bash
./scripts/install-tools.sh
```

### 9.2 Télécharger les documents OWASP

```bash
python3 scripts/fetch_owasp_top10.py
```

Les fichiers Markdown OWASP Top 10:2025 sont téléchargés dans :

```text
knowledge/owasp-top10-2025/
```

### 9.3 Importer dans Open WebUI

Vérifier d'abord les documents détectés :

```bash
.venv/bin/python scripts/load_knowledge.py --dry-run
```

Puis lancer l'importation :

```bash
.venv/bin/python scripts/load_knowledge.py
```

Le script utilise l'API d'Open WebUI.

Il ne crée pas les vecteurs directement dans ChromaDB : Open WebUI orchestre le traitement des documents et Ollama génère les embeddings.

Le nombre de chunks dépend de la configuration de découpage et des documents importés.

## 10. Vérifier ChromaDB et la recherche RAG

Afficher les collections :

```bash
python3 scripts/check_chroma.py
```

Effectuer une recherche :

```bash
python3 scripts/check_chroma.py \
  --query "SQL injection CWE-89 prevention"
```

Le script utilise l'embedding de la question pour rechercher des passages pertinents dans ChromaDB.

Si les collections sont visibles, mais que la recherche échoue avec :

```text
No route to host
```

Vérifier en priorité la connexion à Ollama depuis le conteneur Open WebUI.

## 11. Installer OWASP Report Bridge

Le dépôt contient un outil Python destiné à Open WebUI :

```text
openwebui/tools/owasp_report_bridge.py
```

Cet outil doit être installé manuellement dans Open WebUI.

### Installation

1. Ouvrir **Workspace → Tools**.
2. Créer un nouvel outil.
3. Copier le contenu de `owasp_report_bridge.py`.
4. Enregistrer et activer l'outil.
5. Utiliser le modèle `qwen3.5:9b`.
6. Configurer **Function Calling** en mode **Native**.

Pour les premiers essais, désactiver les **Builtin Tools** et utiliser uniquement le pont OWASP.

### Fonctions disponibles

| Fonction | Description |
|---|---|
| `summarize_latest_zap_report` | Résumer le dernier rapport ZAP |
| `list_zap_findings` | Consulter les alertes détectées |
| `get_zap_finding` | Obtenir le détail d'une alerte |
| `search_owasp_knowledge` | Rechercher dans la documentation OWASP |

Le pont communique avec FastAPI à cette adresse interne :

```text
http://security-agent:8000
```

Vérifier l'accès à FastAPI depuis Open WebUI :

```bash
docker compose exec -T open-webui python -c \
'import urllib.request; print(urllib.request.urlopen("http://security-agent:8000/reports",timeout=10).read().decode()[:1000])'
```

## 12. Importer et analyser les rapports ZAP

Les rapports JSON sont conservés dans :

```text
data/reports/
```

Pour importer un rapport existant :

```bash
python3 scripts/import_zap_report.py \
  /chemin/vers/rapport-zap.json
```

Pour afficher un résumé :

```bash
python3 scripts/summarize_zap_report.py
```

FastAPI permet de consulter les rapports et leurs alertes. Les résultats des scanners doivent toujours être vérifiés avant de conclure à une vulnérabilité confirmée.

**Cette version de l'agent n'exécute pas automatiquement des scans ZAP.**

## 13. Dépannage

### Ollama inaccessible

Symptôme :

```text
No route to host
```

Vérifier :

```bash
grep '^OLLAMA_URL=' .env
curl --connect-timeout 5 http://192.168.2.29:11434/api/tags
```

Tester ensuite depuis Open WebUI.

### ChromaDB unhealthy

Consulter :

```bash
docker inspect mgl805-chromadb \
  --format '{{range .State.Health.Log}}{{println .ExitCode .Output}}{{end}}'

docker compose logs --tail=80 chromadb
```

Vérifier le healthcheck du Compose. Certaines images ChromaDB ne disposent pas de `curl`.

### DVWA ou ZAP inaccessible

Vérifier les publications de ports :

```bash
docker port mgl805-dvwa
docker port mgl805-zap
```

Contrôler :

```bash
docker compose config --quiet
docker compose ps
```

Si nécessaire, recréer les deux services sans toucher aux données MariaDB :

```bash
docker compose up -d --no-deps --force-recreate dvwa zap
```

Vérifier que les ports sont publiés sur l'adresse IP configurée dans `BIND_IP` et que les services utilisent le réseau bridge `access` dans le Compose corrigé.

### Importation OWASP : erreur 401

Vérifier que les clés API sont activées dans Open WebUI et que `OPENWEBUI_API_KEY` est valide.

### ZAP sur le mauvais port

Vérifier :

```bash
grep '^ZAP_GUI_PORT=' .env
```

La valeur doit être :

```dotenv
ZAP_GUI_PORT=8080
```

Puis :

```bash
docker compose up -d --no-deps --force-recreate zap
```

### Diagnostics généraux

```bash
docker compose ps
docker compose logs --tail=80 open-webui
docker compose logs --tail=80 chromadb
docker compose logs --tail=80 security-agent
docker compose logs --tail=80 zap
./scripts/check_stack.sh
```

## 14. Arrêt et sauvegardes

Arrêter le laboratoire :

```bash
./stop.sh
```

Créer une sauvegarde :

```bash
./scripts/backup.sh --yes
```

Exécuter les tests du dépôt :

```bash
./scripts/run-tests.sh
```

Ne pas utiliser `docker compose down -v` si les données persistantes doivent être conservées.

Les sauvegardes peuvent contenir des secrets, des données applicatives et des rapports de sécurité. Elles doivent être protégées.

## 15. Structure du dépôt

```text
mgl805-security-rag-agent/
├── compose.yaml
├── .env.example
├── README.md
├── start.sh
├── stop.sh
├── services/
│   └── security-agent/
│       ├── Dockerfile
│       └── main.py
├── openwebui/
│   └── tools/
│       └── owasp_report_bridge.py
├── scripts/
│   ├── install-tools.sh
│   ├── check_ollama.py
│   ├── check_chroma.py
│   ├── check_stack.sh
│   ├── check_zap_api.sh
│   ├── fetch_owasp_top10.py
│   ├── load_knowledge.py
│   ├── import_zap_report.py
│   ├── summarize_zap_report.py
│   ├── backup.sh
│   └── run-tests.sh
├── knowledge/
│   └── owasp-top10-2025/
├── data/
│   ├── openwebui/
│   ├── chroma/
│   ├── mariadb/
│   ├── zap/
│   ├── reports/
│   └── state/
├── backups/
└── docs/
    ├── ARCHITECTURE.md
    ├── OPERATIONS.md
    ├── SECURITY.md
    └── ROADMAP.md
```

## 16. Documentation supplémentaire

- [Architecture](docs/ARCHITECTURE.md)
- [Opérations et dépannage](docs/OPERATIONS.md)
- [Sécurité](docs/SECURITY.md)
- [Feuille de route](docs/ROADMAP.md)

## 17. Évolutions prévues

Les fonctionnalités suivantes sont prévues pour de futures versions :

- Déclenchement automatisé de scans OWASP ZAP.
- Intégration de Nuclei.
- Connexion sécurisée vers des laboratoires distants avec WireGuard.
- Enrichissement des connaissances à l'aide de NVD, CISA KEV et FIRST EPSS.
- Amélioration de l'orchestration des agents et des rapports.

Ces éléments ne sont pas encore inclus dans le déploiement actuel.

---

**Projet MGL805 — Laboratoire de cybersécurité, intelligence artificielle locale et RAG.**
