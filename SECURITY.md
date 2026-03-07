# Security Policy

Thank you for helping keep Persona Chat safe.

## Supported versions

| Version | Supported |
|---------|-----------|
| Latest on `main` | Best-effort |

## Reporting a vulnerability

Please do **not** open a public GitHub issue for sensitive security reports.

Report privately through **GitHub Security Advisories** — use the "Report a vulnerability" tab on this repository.

## What to include

- Affected version, branch, or commit
- Reproduction steps or proof of concept
- Likely impact and severity estimate
- Suggested mitigation or fix, if you have one

## Response expectations

This is a small, maintainer-driven project. Reports are handled on a **best-effort** basis. We will do our best to acknowledge reports promptly and coordinate a fix before public disclosure, but we cannot guarantee specific response times.

## Scope

The following are in scope:

- Authentication bypass or token manipulation
- Unauthorized file read/write via WebSocket actions
- Code injection through context fields or imported data
- Sensitive data exposure (secrets, auth tokens in logs or exports)

General hardening suggestions and non-sensitive improvements can be submitted as normal issues or pull requests.

## Disclosure

Please allow reasonable time for triage and a fix before any public disclosure. We aim to work collaboratively with reporters to resolve issues responsibly.
