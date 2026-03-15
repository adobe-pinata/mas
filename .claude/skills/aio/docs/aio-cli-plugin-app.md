<!-- Source: https://raw.githubusercontent.com/adobe/aio-cli-plugin-app/master/README.md -->

# aio-cli-plugin-app

## Overview

The aio-cli-plugin-app is a command-line tool for creating, building, and deploying Adobe I/O applications. It's built on oclif and published as an npm package.

## Installation

Users can install this plugin through two methods:

```
$ aio plugins:install -g @adobe/aio-cli-plugin-app
$ aio discover -i
```

## Core Functionality

The plugin provides comprehensive app lifecycle management:

**Creation & Configuration**: Initialize new apps, import Developer Console configurations, and manage workspace settings.

**Component Management**: Add or delete actions, events, extensions, web assets, CI files, and services within existing applications.

**Build & Deploy**: Compile applications with optimization options, deploy to Adobe infrastructure, and manage publishing to Exchange.

**Development**: Run apps locally with hot-reload capabilities, execute test suites (unit and e2e), and access application logs.

**Utilities**: Package apps for distribution, retrieve action URLs, and display app configuration details.

## Key Commands

Notable operations include `aio app build` for compiling assets, `aio app deploy` for publishing changes, `aio app run` for local development, and `aio app test` for validation.

## Configuration Validation

By default, the tool validates configuration files before executing commands, though this can be disabled with the `--no-config-validation` flag.

## Output Formats

Commands support multiple output formats including JSON, YAML, and human-readable variants through various flag options.
