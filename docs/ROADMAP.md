# Feuille de route et périmètre fonctionnel

## Fonctionnalités déjà présentes dans cette version

- Un seul projet Docker Compose réunissant Open WebUI, ChromaDB, Security Agent, ZAP Webswing, DVWA et MariaDB.
- Connexion à Ollama sur Windows configurée par `.env` : il s'agit d'une dépendance externe, non démarrée par Compose.
- Outil Python natif pour l'espace de travail Open WebUI, à installer manuellement, avec quatre fonctions.
- Script de téléchargement des documents officiels OWASP Top 10:2025 ; ingestion authentifiée par l'API d'Open WebUI ; suivi local SHA-256 ; scripts d'inspection ChromaDB et de vérification de la recherche sémantique.
- API FastAPI en lecture seule pour les rapports ZAP et scripts utilitaires pour l'importation de rapports, les résumés, les tests, les vérifications de santé et les sauvegardes.

## Prochaines étapes (NON implémentées dans cette version)

1. **Rétablir l'accès à l'API ZAP sur le port 8090 :** authentifier les appels avec une clé stockée de manière sécurisée et restreindre les clients autorisés. Commencer par ajouter un outil de lecture seule pour l'état de l'API.
2. **Orchestrer les scans :** définir une liste explicite de cibles autorisées, l'approbation de l'utilisateur, les limites de trafic, le suivi d'avancement, l'annulation, des délais d'expiration stricts et la sauvegarde des résultats. Commencer par des analyses non intrusives ; les scans actifs exigent un consentement explicite.
3. **Intégrer Nuclei :** ajouter un moteur distinct et restreint, avec une liste de templates autorisés et une normalisation des résultats. Le LLM ne doit pas pouvoir exécuter librement des templates arbitraires.
4. **Prendre en charge un VLAN distant via WireGuard :** limiter le routage aux services HTTP explicitement autorisés et vérifier que le trafic sortant des conteneurs Docker atteint les cibles sans interconnecter largement les VLAN.
5. **Collecter les renseignements CVE :** synchroniser de façon incrémentale NVD, CISA KEV et FIRST EPSS, avec recherche exacte par identifiant, dédoublonnage, traçabilité des sources et mises à jour planifiées. Utiliser une collection ChromaDB distincte de la base OWASP et conserver les correspondances précises de versions dans un stockage relationnel.
6. **Corréler et produire des rapports :** relier les constats des scanners à OWASP, aux CWE et aux preuves réelles concernant les CVE et les versions. Générer des rapports PDF/JSON révisables en distinguant clairement les faits observés, les hypothèses et les vulnérabilités confirmées.
