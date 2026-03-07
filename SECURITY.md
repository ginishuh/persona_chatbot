# Security Policy

Thank you for helping keep Persona Chat safe.

## Supported versions

| Version | Supported |
|---------|-----------|
| Latest on `main` | Yes |
| Older releases | Best-effort only |

## Reporting a vulnerability

Please do **not** open a public GitHub issue for sensitive security reports.

Report privately through one of these channels:

1. **GitHub Security Advisories** — use the "Report a vulnerability" tab on this repository (if enabled).
2. **Email** — send details to **ginishuh@gmail.com** with the subject `[SECURITY] Persona Chat`.

## What to include

- Affected version, branch, or commit
- Reproduction steps or proof of concept
- Likely impact and severity estimate
- Suggested mitigation or fix, if you have one

## Response timeline

- **Acknowledgement** within 3 business days.
- **Triage and initial assessment** within 7 business days.
- A fix or mitigation will be coordinated before public disclosure.

## Scope

The following are in scope:

- Authentication bypass or token manipulation
- Unauthorized file read/write via WebSocket actions
- Code injection through context fields or imported data
- Sensitive data exposure (secrets, auth tokens in logs or exports)

General hardening suggestions and non-sensitive improvements can be submitted as normal issues or pull requests.

## Disclosure

Please allow reasonable time for triage and a fix before any public disclosure. We aim to work collaboratively with reporters to resolve issues responsibly.
