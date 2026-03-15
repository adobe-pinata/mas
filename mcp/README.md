# MCP Server Configurations

This directory contains Model Context Protocol (MCP) server configurations for various integrations.

## Available Configurations

### 1. AEM Content Services (`.mcp.aem.json`)

Provides access to Adobe Experience Manager content services through the Odin MCP server.

**Environment Variables Required:**
- `AEM_ACCESS_TOKEN` - Your Adobe IMS access token
- `AEM_AUTHOR_URL` - AEM author instance URL (e.g., `https://author-p22655-e155390.adobeaemcloud.com`)

**Setup:**
1. Ensure your `.env` file contains the required variables:
   ```env
   AEM_ACCESS_TOKEN="your-token-here"
   AEM_AUTHOR_URL="https://author-p22655-e155390.adobeaemcloud.com"
   ```

2. Start Claude Code with the AEM MCP configuration:
   ```bash
   claude --mcp-config mcp/.mcp.aem.json
   ```

   The configuration will automatically load environment variables from your `.env` file.

**Features:**
- Search and list content fragment models
- Get content fragments and their data
- Search content fragments
- Preview content delivery
- Manage localization and translations
- Handle publication workflows

### 2. Playwright (`.mcp.playwright.json`)

Browser automation and testing through Playwright MCP.

**Configuration:** `.mcp.playwright.config.json`
- Chromium browser in headless mode
- 1920x1080 viewport
- Video recording enabled

### 3. Legacy Loki Configuration (`.mcp.loki.json`)

⚠️ **Deprecated:** This file contains hardcoded credentials. Use `.mcp.aem.json` instead.

## Usage

To use any of these MCP configurations with Claude Code, pass the configuration file path when starting a session:

```bash
# AEM Content Services
claude --mcp-config mcp/.mcp.aem.json

# Playwright
claude --mcp-config mcp/.mcp.playwright.json

# Multiple configurations (if supported)
claude --mcp-config mcp/.mcp.aem.json --mcp-config mcp/.mcp.playwright.json
```

## Security Notes

- Never commit actual tokens to git
- Keep your `.env` file private and add it to `.gitignore`
- Rotate your AEM access tokens regularly
- Use the `.env.sample` file as a template for required environment variables
