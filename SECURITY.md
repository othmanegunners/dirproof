# Security policy

## Supported versions

Security fixes target the latest release on the default branch. This project is early-stage and the format may evolve.

## Reporting vulnerabilities

Please do not post exploit details, credentials, or sensitive file contents in a public issue. Contact the maintainer through the GitHub profile or use GitHub's private vulnerability reporting feature if enabled. If no private channel is available, open a general issue *without sensitive details* to request secure contact.

## Threat model

dirproof helps find accidental or unexpected changes by comparing SHA-256 hashes. It is **not** a malware scanner, digital signature system, or secure backup. If an attacker can modify the files and their manifest, the comparison cannot authenticate either. Store trusted manifests in a separate, protected location.

The tool deliberately skips symbolic links to avoid following them outside the selected directory. As with any scanner, files could be modified concurrently, so snapshots of actively changing directories may be inconsistent.
