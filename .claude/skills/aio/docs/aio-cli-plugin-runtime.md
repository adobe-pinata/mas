<!-- Source: https://raw.githubusercontent.com/adobe/aio-cli-plugin-runtime/master/README.md -->

# Adobe I/O Runtime CLI Plugin (aio-cli-plugin-runtime)

## Overview

The `aio-cli-plugin-runtime` is an Adobe I/O CLI plugin that provides comprehensive command-line management of Adobe I/O Runtime resources. Built on the oclif framework, it enables developers to manage actions, packages, triggers, rules, APIs, and other runtime assets directly from the terminal.

## Installation

Users can install the plugin through two methods:

```sh-session
$ aio plugins:install @adobe/aio-cli-plugin-runtime
$ # OR
$ aio discover -i
$ aio runtime --help
```

## Core Functionality

The plugin organizes commands into logical categories:

**Action Management**: Create, update, delete, invoke, and list serverless functions with support for parameters, environment variables, memory/timeout configuration, and Docker images.

**Package Operations**: Organize actions into packages with parameter binding, sharing controls, and lifecycle management capabilities.

**Trigger & Rule Management**: Define event triggers, create rules connecting triggers to actions, and manage automation workflows.

**API Route Configuration**: Expose actions as HTTP endpoints with configurable base paths, HTTP verbs, and response types.

**Activation Monitoring**: Track function executions, retrieve logs, results, and activation details for debugging and observability.

**Namespace Administration**: Manage multiple namespaces, configure log forwarding to external services (Splunk, New Relic, Azure), and view namespace properties.

**Deployment Tools**: Deploy projects using manifest files, export managed assets, and manage deployment lifecycles with sync and undeploy operations.

## Common Configuration Options

Most commands accept standard authentication and connection parameters:
- Authentication via `-u` or `--auth` flags
- Custom API hosts and versions
- Client certificates for secure connections
- Verbose output and debug modes

## Key Features

The plugin supports advanced capabilities including web actions, action sequences, parameter files (JSON), annotation management, log filtering with timestamps, continuous log streaming, and recursive package deletion with associated rules and triggers.

## Project Information

**License**: Apache License 2.0
**Repository**: Adobe's GitHub repository for the aio-cli-plugin-runtime
**Contributing**: Guidelines available in the CONTRIBUTING.md file
