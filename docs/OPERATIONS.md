# Exploitation et dépannage

## Erreur « Model qwen3.5:9b not found »

Ce message peut signifier qu'Ollama est **inaccessible**, et non que le modèle est absent. Sur Windows, exécutez `ollama list`, `ollama ps`, puis `curl.exe http://127.0.0.1:11434/api/tags`. Sur la VM Linux, essayez `curl --max-time 8 http://WINDOWS_IP:11434/api/tags`. Depuis l'environnement Open WebUI, `./scripts/check_stack.sh` vérifie la connexion configurée. Vérifiez l'adresse IPv4 actuelle du PC Windows, l'interface d'écoute définie par `OLLAMA_HOST`, les règles du Pare-feu Windows, les routes et la valeur `OLLAMA_URL` de `.env`. Le pont réutilise cette URL grâce aux variables d'environnement du conteneur.

## L'outil personnalisé d'Open WebUI affiche « No tools found »

Utilisez l'**outil Python de l'espace de travail (Workspace Tool)** fourni dans `openwebui/tools/owasp_report_bridge.py`. Cette solution a été validée dans notre laboratoire, alors qu'une connexion externe de type OpenAPI affichait `No tools found`. Dans le profil du modèle, désactivez **Builtin Tools**, choisissez **Function Calling = Native**, activez le pont et démarrez une nouvelle conversation. Confirmez que les quatre fonctions apparaissent. Le simple fait que le modèle affirme ne pas avoir d'outils ne prouve pas une panne réseau : vérifiez la liste des appels réellement exécutés et le comportement du backend.

## L'ajout automatique de connaissances empêche les appels d'outils

Dans nos essais, Qwen3.5 9B a parfois répondu directement à partir des documents récupérés (par exemple, 11 sources) sans appeler les outils FastAPI. Testez d'abord les outils personnalisés sans base de connaissances jointe automatiquement, puis appelez explicitement `search_owasp_knowledge`. Si un autre modèle gère correctement le RAG automatique et les outils, vous pourrez réactiver ce mode après validation.

## ZAP affiche Webswing, mais son API ferme la connexion

Le port 8080 du conteneur sert Webswing et est publié sur le port 8088 de l'hôte. **Ce n'est pas le port de l'API.** Le port 8090 héberge l'API/le proxy de ZAP, mais ZAP doit d'abord être initialisé en ouvrant `/zap` dans le navigateur. Dans l'ancien environnement, le port 8090 renvoyait `RemoteDisconnected`, même depuis l'intérieur du conteneur ZAP : ce problème **n'a pas été résolu**. Vérifiez **Tools → Options → API** (clé API et adresses autorisées), **Network → Local Servers/Proxies** (adresse d'écoute et mode API/proxy), ainsi que les journaux de ZAP. `./scripts/check_zap_api.sh` permet d'interroger la version avec authentification, en lecture seule. Ne publiez pas le port 8090 et ne désactivez pas l'authentification API pour contourner le problème.

## Importation des rapports et permissions

Les rapports enregistrés doivent contenir un tableau `site` au premier niveau. Utilisez :

```bash
python3 scripts/import_zap_report.py /path/to/report.json
python3 scripts/summarize_zap_report.py
```

Si la fenêtre de génération de rapport ZAP produit `report.html`, exportez également un fichier distinct `report.json` : le parseur FastAPI ne sait pas lire les formats HTML ou PDF. ZAP enregistre les rapports dans `/zap/wrk/reports`, ce qui correspond au dossier hôte `data/reports`. Le répertoire `/reports` monté dans FastAPI est en lecture seule. Si les fichiers n'apparaissent pas, vérifiez les permissions du dossier hôte et `docker compose exec security-agent ls -l /reports` (si `ls` est disponible ; l'image Python utilisée est minimale).

## Problèmes d'importation des connaissances

- La clé API doit provenir du compte Open WebUI prévu pour l'opération ; ne la partagez jamais publiquement.
- Un **identifiant de base de connaissances (Knowledge ID)** est distinct d'un identifiant de fichier ou de modèle.
- Le traitement des fichiers est asynchrone : le script attend l'état `completed` avant d'appeler `file/add`.
- Une erreur de contenu dupliqué peut signifier que le document est déjà indexé. Évitez d'exécuter `--force` en boucle sans diagnostic.
- Si `check_chroma.py` n'identifie aucune collection configurée, corrigez `KNOWLEDGE_ID` dans `.env`, puis recréez **uniquement Open WebUI** avec `docker compose up -d --no-deps --force-recreate open-webui`.
- Si vous changez de modèle d'embedding, recalculez les vecteurs et réindexez les documents dans une nouvelle collection. Des dimensions identiques ne garantissent pas que les vecteurs appartiennent au même espace sémantique.
- Les importations volumineuses peuvent durer plusieurs minutes, car Ollama est exécuté sur une autre machine.

## Sauvegardes et mises à niveau

Utilisez `./scripts/backup.sh --yes` pour une copie cohérente des données hors ligne (le stack est arrêté pendant la création de l'archive). La sauvegarde contient `.env`, les données des comptes, ChromaDB et MariaDB, les rapports et les clés de l'autorité de certification ZAP. Sécurisez ou chiffrez cette archive. N'exécutez `docker compose pull && docker compose up -d --build` qu'après avoir lu les notes de version et créé une sauvegarde. Conservez les valeurs stables de `.env` pour préserver les sessions Open WebUI et les identifiants de base de données. **N'exécutez pas** `docker compose down -v`, sauf si vous souhaitez détruire volontairement les données.

## Autres commandes de diagnostic

```bash
docker compose config --quiet
docker compose ps
docker compose logs --tail=100 chromadb
docker compose logs --tail=100 zap
docker compose exec -T open-webui python -c 'import urllib.request; print(urllib.request.urlopen("http://security-agent:8000/reports").read().decode())'
python3 scripts/check_chroma.py --query 'SQL injection CWE-89'
./scripts/run-tests.sh
```
