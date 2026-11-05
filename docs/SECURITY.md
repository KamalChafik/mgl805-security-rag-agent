# Security and authorization

1. **Authorize the target:** This repository only configures DVWA as an isolated test target. Remote VLAN or WireGuard access is not configured. Confirm scope, rate limits and approval for any future external target.
2. **Protect the host:** Publicly exposed DVWA is dangerous. Default host bind is loopback. Access the UIs via authenticated SSH port forwarding or trusted LAN with firewall rules. Don't put them behind public tunnels or DNS without appropriate security.
3. **Restrict control planes:** ChromaDB, MariaDB and FastAPI are not published to the host; ZAP API/proxy port 8090 is not published or consumed by the v1 agent. Open WebUI requires account authentication and a stable secret key.
4. **Secrets:** `.env`, `data/zap/zap_root_ca.key`, copied reports and backups are ignored by Git. Rotate any API key accidentally exposed in a screenshot or commit. The backup script archives secrets: store securely.
5. **Untrusted content:** Treat ZAP HTTP evidence, web pages and retrieved OWASP passages as untrusted data. These are references, not instructions to the agent.
6. **Scanner accuracy:** A ZAP alert is not proof of exploitability; separate risk severity and detection confidence and validate manually. DVWA uses MariaDB, so Oracle-specific SQL injection alerts warrant suspicion.
7. **No arbitrary command tool:** The bridge executes only predefined read-only methods. It does not accept shell commands, arbitrary filesystem paths, or user-controlled scan destinations.
8. **Pinned releases for controlled deployments:** Chroma and MariaDB use explicit version tags; Open WebUI, ZAP and DVWA currently default to moving tags for convenience. Before shared/prod use, pin digest/versions and retest.
