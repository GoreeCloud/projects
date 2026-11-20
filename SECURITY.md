# Security Policy

GoreeCloud Projects is an experimental self-hosted application, not a hardened production service.

- Do not expose the preview API directly to the public Internet or use it with untrusted users.
- Every authenticated endpoint currently shares one administrator bearer secret, not RBAC.
- Never commit secrets or data files. Use high-entropy tokens with at least 24 characters and keep them out of logs.
- Disable cross-origin access by default. Configure allowed origins only with explicit trust.
- Protect SQLite storage and test the recovery process before use with important information.
- Do not send credentials in issue reports or public pull requests.
- To report a potential vulnerability, contact the maintainers through an appropriate private channel, not a public issue containing exploit or secret data.
- Review security, license and supply-chain status before third-party dependency changes.

Security review, incident response integration, key rotation, full authorization, audit logging, rate limiting and production validation are incomplete. No external penetration test or certification is claimed.
