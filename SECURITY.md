# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### Private Reporting (Preferred)

Use GitHub's **Private Vulnerability Reporting** feature:
1. Go to the [Security tab](https://github.com/martymcenroe/Aletheia/security)
2. Click "Report a vulnerability"
3. Fill out the form with details

### Email

Alternatively, email security concerns to the repository owner (see GitHub profile).

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment:** Within 48 hours
- **Initial Assessment:** Within 1 week
- **Resolution Target:** Within 30 days (severity dependent)

### Scope

This policy covers:
- The Aletheia browser extension (Chrome/Firefox)
- The AWS Lambda backend
- This repository's code and configuration

### Out of Scope

- Third-party dependencies (report to upstream)
- Social engineering attacks
- Denial of service attacks

## Security Measures

Aletheia implements several security measures:
- **Privacy-first permissions** (ADR 0201) - No `<all_urls>` permission
- **Content Security Policy** - Strict CSP in Manifest V3
- **Input validation** - All user input validated before processing
- **No PII storage** - User text processed in-memory only
- **HTTPS only** - All API communication encrypted
- **Pre-commit hooks** - Secret scanning via gitleaks

## Acknowledgments

We appreciate responsible disclosure and will acknowledge security researchers who report valid vulnerabilities (with permission).
