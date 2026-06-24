# Security Policy

## Supported Versions

Security fixes are provided for the latest released version.

## Reporting a Vulnerability

Please report security issues privately through the repository security advisory
feature, or by contacting the maintainers listed in the project repository.

Do not open a public issue for vulnerabilities that could expose user data,
allow unwanted filesystem access, or cause denial of service.

## Scope

Holy Water stores templates, fragments, and generation history in SQLite. Treat
database paths and API deployment configuration as trusted administrative input.
