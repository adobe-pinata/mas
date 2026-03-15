<!-- Source: https://raw.githubusercontent.com/adobe/aio-cli/master/README.md -->

# Adobe I/O Extensible CLI (aio-cli)

## Overview

The **aio-cli** is Adobe's extensible command-line interface built on oclif. It serves as "Adobe I/O Extensible CLI" for managing applications and services.

## Key Features

The CLI provides comprehensive command families for:

- **App Management**: Creating, building, deploying, and testing Adobe I/O Apps
- **Authentication**: Login/logout and context management via Adobe IMS
- **Runtime Operations**: Managing serverless actions, packages, triggers, and rules
- **Console Integration**: Organization, project, and workspace selection
- **Configuration**: Persistent storage of settings and credentials
- **Certificates**: Generation and verification of security certificates
- **Events**: Management of Adobe I/O event registrations and providers
- **State Management**: Key-value storage with regional support

## Technical Stack

The project uses:
- Node.js runtime
- oclif framework for CLI structure
- Apache 2.0 licensing
- Automated CI/CD via GitHub Actions
- Code coverage tracking through Codecov

## Proxy Configuration

The CLI supports HTTP/HTTPS proxies through environment variables (`HTTP_PROXY` and `HTTPS_PROXY`), with credentials embeddable in URLs when basic authentication is required.

## Getting Started

Installation is straightforward via npm, and the documentation references the broader App Builder documentation at developer.adobe.com for comprehensive setup guidance.
