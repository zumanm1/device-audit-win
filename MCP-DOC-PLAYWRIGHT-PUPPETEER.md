# Model Context Protocol (MCP) Documentation: Playwright & Puppeteer

**Author:** Cascade AI  
**Date:** May 23, 2025  
**Version:** 1.0.0

## Overview

This document provides comprehensive details about the Playwright and Puppeteer Model Context Protocol (MCP) servers installed in this environment. MCP servers extend AI systems by providing access to specialized functions, external information, and services. In this case, both servers enable browser automation capabilities.

## 1. Server Status and Installation Details

### 1.1 Playwright MCP

**Status:** Running but requires `--no-sandbox` configuration  
**Process ID:** 348945  
**Command:** `node /root/.npm/_npx/9833c18b2d85bc59/node_modules/.bin/mcp-server-playwright`  
**Parent Process:** npm exec @playwright/mcp@latest (PID: 348915)  

### 1.2 Puppeteer MCP

**Status:** Running and fully operational  
**Process ID:** 348970  
**Command:** `node /root/.npm/_npx/ab5cd9f6d13a2312/node_modules/.bin/mcp-server-puppeteer`  
**Parent Process:** npm exec @modelcontextprotocol/server-puppeteer (PID: 348958)  

### 1.3 Browser Instances

Puppeteer is using a Chrome instance with the following characteristics:
- Path: `/root/.cache/puppeteer/chrome/linux-131.0.6778.204/chrome-linux64/chrome`
- Version: 131.0.6778.204
- Debugging port: 37097 (TCP on 127.0.0.1)
- Headless mode: Enabled

## 2. Network Configuration

### 2.1 Listening Ports

| Server    | IP Address | Port  | Protocol | Status  |
|-----------|------------|-------|----------|---------|
| Puppeteer | 127.0.0.1  | 37097 | TCP      | LISTEN  |

### 2.2 Browser Remote Debugging

Puppeteer has a Chrome instance with remote debugging enabled on port 37097.

## 3. Usage Examples

### 3.1 Puppeteer MCP (Working)

```javascript
// Navigate to a URL
mcp2_puppeteer_navigate({
  url: "https://example.com",
  allowDangerous: true,
  launchOptions: {"headless": true, "args": ["--no-sandbox"]}
});

// Take a screenshot
mcp2_puppeteer_screenshot({
  name: "example_screenshot"
});

// Click an element
mcp2_puppeteer_click({
  selector: "#submit-button"
});

// Fill out a form
mcp2_puppeteer_fill({
  selector: "#username",
  value: "testuser"
});

// Execute JavaScript
mcp2_puppeteer_evaluate({
  script: "document.title"
});
```

### 3.2 Playwright MCP (Requires Configuration)

```javascript
// This will fail without proper configuration
mcp0_browser_navigate({
  url: "https://example.com"
});

// Other Playwright commands (need configuration to work)
mcp0_browser_snapshot();
mcp0_browser_click({
  element: "Submit button",
  ref: "button[type='submit']"
});
```

## 4. Configuration Issues and Solutions

### 4.1 Playwright Sandbox Issue

**Issue:** Playwright fails with error: `Running as root without --no-sandbox is not supported`

**Solution:** The Playwright MCP server needs to be launched with Chrome sandbox disabled. This is a security limitation when running browsers as root.

1. Edit the MCP configuration file:
   ```bash
   vi /root/.config/playwright-mcp/config.json
   ```

2. Add the following configuration:
   ```json
   {
     "launchOptions": {
       "args": ["--no-sandbox", "--disable-setuid-sandbox"]
     }
   }
   ```

3. Restart the Playwright MCP server:
   ```bash
   pkill -f mcp-server-playwright
   npm exec @playwright/mcp@latest
   ```

### 4.2 Puppeteer Configuration (Working)

Puppeteer is correctly configured with the `--no-sandbox` flag and works properly. When using Puppeteer MCP functions, always include:

```javascript
{
  allowDangerous: true,
  launchOptions: {"headless": true, "args": ["--no-sandbox"]}
}
```

## 5. Tool Command Reference

### 5.1 Playwright MCP Commands

| Command | Description | Parameters |
|---------|-------------|------------|
| `mcp0_browser_navigate` | Navigate to a URL | `url`: The URL to navigate to |
| `mcp0_browser_snapshot` | Capture accessibility snapshot | None |
| `mcp0_browser_click` | Click an element | `element`: Human-readable description, `ref`: Element reference |
| `mcp0_browser_type` | Type text into an element | `element`, `ref`, `text`, `slowly`, `submit` |
| `mcp0_browser_take_screenshot` | Take a screenshot | `element`, `ref`, `filename`, `raw` |
| `mcp0_browser_wait_for` | Wait for text or time | `text`, `textGone`, `time` |

### 5.2 Puppeteer MCP Commands

| Command | Description | Parameters |
|---------|-------------|------------|
| `mcp2_puppeteer_navigate` | Navigate to a URL | `url`, `allowDangerous`, `launchOptions` |
| `mcp2_puppeteer_screenshot` | Take a screenshot | `name`, `selector`, `width`, `height`, `encoded` |
| `mcp2_puppeteer_click` | Click an element | `selector` |
| `mcp2_puppeteer_fill` | Fill a form field | `selector`, `value` |
| `mcp2_puppeteer_evaluate` | Execute JavaScript | `script` |
| `mcp2_puppeteer_hover` | Hover over an element | `selector` |
| `mcp2_puppeteer_select` | Select an option | `selector`, `value` |

## 6. Security Considerations

1. **Sandbox Disabled**: Both MCP servers are running with the sandbox disabled (`--no-sandbox`). This is required when running as root but reduces security isolation.

2. **Root Execution**: The browsers are running as root, which is not recommended for production environments.

3. **Network Access**: The browser instances have full network access and can make external requests.

4. **Local File Access**: The browsers can access the local file system with root permissions.

## 7. Troubleshooting

### 7.1 Playwright Issues

- If Playwright fails with sandbox errors, ensure the configuration includes `--no-sandbox`
- Check if the browser binary exists and is executable
- Verify the MCP server process is running

### 7.2 Puppeteer Issues

- Always include `allowDangerous: true` and the `--no-sandbox` flag in `launchOptions`
- If screenshots fail, check for sufficient disk space
- For navigation timeouts, increase the default timeout value

## 8. Additional Resources

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Puppeteer Documentation](https://pptr.dev/)
- [Model Context Protocol Specification](https://github.com/microsoft/modelcontextprotocol)

## 9. Conclusion

Both Playwright and Puppeteer MCP servers provide powerful browser automation capabilities. Puppeteer is fully operational in the current environment, while Playwright requires additional configuration to work with root privileges. When properly configured, both provide similar capabilities for browser automation, enabling AI systems to interact with web content.
