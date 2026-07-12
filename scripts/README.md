# Scripts

Utility scripts for development, deployment, and maintenance of Sona AI OS.

## Purpose

This directory contains automation scripts for common development and operations tasks:

- **Setup**: Environment initialization and dependency installation
- **Build**: Build automation and packaging
- **Deploy**: Deployment scripts for various environments
- **Database**: Migration and seeding scripts
- **Testing**: Test runner and coverage scripts
- **Maintenance**: Cleanup, backup, and health checks

## Usage

All scripts should be executable and well-documented. Run from the project root:

```bash
./scripts/<script-name>.sh
```

## Conventions

- Use Bash for shell scripts with `#!/usr/bin/env bash`
- Include usage documentation at the top of each script
- Use `set -euo pipefail` for error handling
- Support `--help` flag for all scripts
- Keep scripts idempotent where possible
