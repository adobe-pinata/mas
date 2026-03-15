<!-- Source: https://developer.adobe.com/app-builder/docs/get_started/app_builder_get_started/first_app/ -->

# Creating Your First App Builder Application

## Overview

This comprehensive guide walks developers through setting up and developing an App Builder application, from initial environment configuration through deployment.

## Key Setup Steps

**Environment Verification**: Before beginning, ensure you have "access to App Builder" and that your "local environment and tooling are up to date."

**Developer Console Project Creation**: Start by creating a new project in Adobe Developer Console, which provides "access to APIs, SDKs and Developer tools to integrate and extend Adobe products."

**CLI Authentication**: Sign in using `aio login`, which opens a browser window for Adobe ID authentication. The CLI automatically stores tokens for subsequent use.

## Project Initialization Options

The guide describes three initialization paths:

1. **Enterprise Users with Extension Points**: Use `aio app init <app_name>` to select from pre-configured extension points and templates.

2. **Enterprise Users (Empty Project)**: Use `aio app init <app_name> --standalone-app` to bootstrap with custom feature selection including Actions, Events, Web Assets, and CI/CD.

3. **Non-Enterprise Developers**: Options include importing credentials via `aio app init <app_name> --import <path>` or initializing without credentials using the `-y` flag.

## Project Structure

A bootstrapped application includes:

- **src/**: Extension point folders containing both actions and front-end resources
- **app.config.yaml**: Master configuration file
- **.env**: Environment variables with credentials (excluded from version control)
- **.aio**: CLI configuration variables
- **test/ and e2e/**: Testing directories

## Local Development

Run applications using `aio app dev` (preferred for development with hot reload) or `aio app run` (for testing runtime-specific functionality). The development server runs on localhost with automatic SSL certificate generation.

## Deployment

Execute `aio app deploy` to build and deploy actions to Adobe I/O Runtime and front-end assets to the CDN. The command outputs deployment URLs for both standalone and Experience Cloud Shell access.

## Common Troubleshooting

- Keep CLI updated via `npm install -g @adobe/aio-cli`
- Authorization errors require passing valid tokens in request headers
- Missing parameter errors indicate required action inputs weren't provided
