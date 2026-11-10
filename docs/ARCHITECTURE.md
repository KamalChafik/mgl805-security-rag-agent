# Architecture — Laboratoire de sécurité MGL805

## Répartition des composants

La VM Linux héberge Open WebUI, ChromaDB, FastAPI, ZAP Webswing, DVWA et MariaDB dans un seul projet Docker Compose. Ollama (`qwen3.5:9b` et `qwen3-embedding:0.6b`) continue de fonctionner sur le PC Windows équipé d'une RTX 3060 de 12 Go. Ce choix est volontaire : utiliser **un seul projet Compose** ne signifie pas que tous les composants doivent être exécutés sur la même machine physique.

## Deux flux distincts

**Ingestion des connaissances (gérée par Open WebUI) :** fichiers officiels OWASP → `scripts/load_knowledge.py`, au moyen de l'API d'Open WebUI → traitement et découpage des fichiers par Open WebUI → calcul des embeddings par Ollama → écriture des vecteurs, des fragments de texte et des métadonnées dans ChromaDB par Open WebUI. Le script de chargement ne contourne pas Open WebUI.

**Exécution de l'agent (appels d'outils explicites) :** utilisateur → Open WebUI/Qwen → `OWASP Report Bridge`. Le pont lit les constats ZAP dans FastAPI par HTTP et récupère les fragments OWASP en demandant l'embedding de la requête à Ollama, puis en interrogeant la collection ChromaDB existante. Le modèle met ensuite les deux sources en relation. Pour cette configuration, évitez de joindre automatiquement un contexte documentaire volumineux lorsque vous testez les appels d'outils.

## Isolation Docker

- `backend` : Open WebUI, ChromaDB et FastAPI. Open WebUI et le pont peuvent communiquer avec l'API Ollama externe sur Windows. Aucun port de ChromaDB ni de FastAPI n'est publié sur l'hôte.
- `lab` (interne) : ZAP, DVWA et FastAPI, isolés volontairement des destinations externes. ZAP et l'agent accèdent à DVWA par `http://dvwa:80/`.
- `dbnet` (interne) : DVWA et MariaDB uniquement. MariaDB ne doit pas être accessible à ZAP ni aux autres conteneurs applicatifs.

L'interface Webswing de ZAP est publiée sur le port 8088 de l'hôte. Le port interne 8090, utilisé par le proxy et l'API de contrôle, n'est pas publié. Les clés de l'autorité de certification racine de ZAP se trouvent sous `data/zap/`. FastAPI accède à `data/reports/` uniquement en lecture.

## Limites actuelles

- La cible du laboratoire est DVWA, et non l'environnement distant Juice Shop d'un collègue.
- Aucune fonction API ne permet encore de lancer un scan. Son ajout nécessitera des contrôles d'autorisation, un périmètre de cibles strict et une approbation explicite avant tout test intrusif.
- L'UUID exact de la collection ChromaDB est créé lors de la création de la base de connaissances. Les documents sources peuvent produire plus ou moins de 161 fragments selon les paramètres de découpage.
- Les valeurs du fichier `.env` côté hôte ne remplacent pas nécessairement les paramètres déjà enregistrés dans l'interface d'administration d'Open WebUI. Vérifiez la configuration réellement active.
