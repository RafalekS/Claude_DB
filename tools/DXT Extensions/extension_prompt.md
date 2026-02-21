# DXT Extension Development Framework - General Prompt

## CRITICAL INSTRUCTIONS - READ FIRST

**DO NOT ASSUME ANYTHING. ASK QUESTIONS IF UNCLEAR.**

**DEPENDENCY RULE:** NEVER use `@modelcontextprotocol/sdk` or ANY external dependencies in DXT extensions. Dependencies are NOT bundled in .dxt files and will cause `Cannot find package` errors. Always create standalone MCP server implementations that handle the protocol directly.

**FILE ACCESS:** I have direct filesystem access to `C:\Users\USERNAME\Downloads\claude\` - use this to create/modify files directly instead of providing code in artifacts.

**NO BUILD SCRIPTS:** Don't create PowerShell build scripts unless specifically requested. Provide manual commands instead.

## EXTENSION DEVELOPMENT FRAMEWORK

### Project Setup
1. **Extension Directory:** `C:\Users\USERNAME\Downloads\claude\[extension_name]\`
2. **File Structure:**
   ```
   [extension_name]/
   ├── manifest.json          # DXT 0.1 compliant metadata
   ├── package.json           # NO dependencies field!
   ├── server/
   │   └── index.js           # Standalone MCP server
   ├── README.md              # Documentation
   └── dist/
       └── [extension_name].dxt # Built extension package
   ```

### Required Files

#### manifest.json (DXT 0.1 Specification)
```json
{
  "dxt_version": "0.1",
  "name": "[extension_name]",
  "version": "1.0.0", 
  "display_name": "[Human Readable Name]",
  "description": "[Brief description]",
  "author": { "name": "RLS" },
  "license": "MIT",
  "server": {
    "type": "node",
    "entry_point": "server/index.js",
    "mcp_config": {
      "command": "node",
      "args": ["${__dirname}/server/index.js"],
      "env": {
        // User config variables here
      }
    }
  },
  "tools": [
    // Tool definitions here
  ],
  "user_config": {
    // User configuration options here
  },
  "compatibility": {
    "platforms": ["win32"],
    "runtimes": { "node": ">=18.0.0" }
  }
}
```

#### package.json (NO DEPENDENCIES!)
```json
{
  "name": "[extension_name]_dxt",
  "version": "1.0.0",
  "description": "[Extension description]",
  "main": "server/index.js",
  "type": "module",
  "scripts": {
    "start": "node server/index.js"
  },
  "author": "RLS",
  "license": "MIT",
  "engines": { "node": ">=18.0.0" },
  "os": ["win32"]
}
```

### Standalone MCP Server Template

**CRITICAL:** Never import external packages. Implement MCP protocol directly:

```javascript
#!/usr/bin/env node

/**
 * [Extension Name] MCP Server - STANDALONE VERSION
 * No external dependencies - implements basic MCP protocol directly
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const execAsync = promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class Standalone[ExtensionName]Server {
  constructor() {
    this.capabilities = { tools: {} };
    
    // Configuration from environment variables (set by DXT host)
    this.config = {
      // Map user_config variables from manifest
    };
    
    this.tools = [
      // Tool definitions with inputSchema
    ];
  }

  sendResponse(id, result) {
    const response = { jsonrpc: '2.0', id: id, result: result };
    console.log(JSON.stringify(response));
  }

  sendError(id, code, message) {
    const response = { 
      jsonrpc: '2.0', 
      id: id, 
      error: { code: code, message: message } 
    };
    console.log(JSON.stringify(response));
  }

  async handleRequest(request) {
    const { method, params, id } = request;

    try {
      // Handle notifications (no id field, no response expected)
      if (id === undefined) {
        switch (method) {
          case 'notifications/initialized':
            return;
          default:
            return;
        }
      }

      // Handle regular requests (have id field, response expected)
      switch (method) {
        case 'initialize':
          this.sendResponse(id, {
            protocolVersion: '2024-11-05',
            capabilities: this.capabilities,
            serverInfo: {
              name: '[extension_name]',
              version: '1.0.0'
            }
          });
          break;

        case 'tools/list':
          this.sendResponse(id, { tools: this.tools });
          break;

        case 'tools/call':
          const result = await this.callTool(params.name, params.arguments || {});
          this.sendResponse(id, result);
          break;

        case 'resources/list':
        case 'prompts/list':
          this.sendError(id, -32601, `Method not found: ${method}`);
          break;

        default:
          this.sendError(id, -32601, `Method not found: ${method}`);
      }
    } catch (error) {
      if (id !== undefined) {
        this.sendError(id, -32603, `Internal error: ${error.message}`);
      }
    }
  }

  async callTool(name, args) {
    switch (name) {
      // Implement your tools here
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  }

  run() {
    console.error('[Extension Name] MCP server running on stdio');
    
    process.stdin.setEncoding('utf8');
    
    let buffer = '';
    process.stdin.on('data', (chunk) => {
      buffer += chunk;
      const lines = buffer.split('\n');
      buffer = lines.pop(); // Keep incomplete line in buffer
      
      for (const line of lines) {
        if (line.trim()) {
          try {
            const request = JSON.parse(line.trim());
            this.handleRequest(request);
          } catch (error) {
            console.error('Failed to parse request:', error.message);
          }
        }
      }
    });

    process.stdin.on('end', () => {
      process.exit(0);
    });
  }
}

const server = new Standalone[ExtensionName]Server();
server.run();
```

## DEVELOPMENT PROCESS

### 1. Requirements Gathering
- **Ask questions** about functionality, user interface, configuration needs
- **Clarify triggers** - natural language detection, specific commands, etc.
- **Define tools** - what capabilities should the extension provide
- **Specify configuration** - what settings users need to customize

### 2. Implementation Steps
1. **Create directory structure** in `C:\Users\USERNAME\Downloads\claude\[extension_name]\`
2. **Write manifest.json** following DXT 0.1 specification
3. **Create package.json** with NO dependencies
4. **Implement standalone MCP server** in `server/index.js`
5. **Write README.md** with usage instructions
6. **Build extension** using manual command

### 3. Tool Implementation Pattern
Each tool should return this structure:
```javascript
return {
  content: [
    {
      type: 'text',
      text: JSON.stringify({
        success: true/false,
        data: /* relevant data */,
        error: /* error message if failed */
      }, null, 2)
    }
  ]
};
```

### 4. User Configuration
- **Environment Variables:** Map user_config to process.env in server
- **Default Values:** Always provide sensible defaults
- **Validation:** Handle missing or invalid configuration gracefully

## BUILD PROCESS

### Manual Build Command
```powershell
cd "C:\Users\USERNAME\Downloads\claude\[extension_name]"
Compress-Archive -Path manifest.json,package.json,server,README.md -DestinationPath dist\[extension_name].dxt -Force
```

### Verification
```powershell
Get-Item dist\[extension_name].dxt | Select-Object Name, Length, LastWriteTime
```

## CRITICAL ISSUES TO AVOID

### 1. Dependency Error (MOST COMMON)
- **Problem:** Using `@modelcontextprotocol/sdk` or other npm packages
- **Symptom:** `Cannot find package` error when extension loads
- **Solution:** Implement MCP protocol directly using only Node.js built-ins

### 2. File Creation Method
- **Wrong:** Creating artifacts and asking user to save files
- **Right:** Using filesystem access to create files directly

### 3. Build Scripts
- **Wrong:** Creating complex PowerShell scripts
- **Right:** Providing simple manual commands

### 4. Assumptions
- **Wrong:** Implementing without asking clarifying questions
- **Right:** Confirming requirements before coding

## COMMON PATTERNS

### State Management
- Use JSON files in extension directory for persistence
- Handle file read/write errors gracefully
- Provide default state when files don't exist

### Error Handling
- Always wrap tool calls in try-catch
- Return structured error responses
- Log errors to stderr for debugging

### Command Execution
- Use `exec` with promisify for external commands
- Set appropriate timeouts
- Handle both stdout and stderr

### File Operations
- Use `fs/promises` for async file operations
- Create directories recursively with `{ recursive: true }`
- Handle encoding properly (`utf8` for text files)

## TESTING APPROACH

### Manual Testing
1. **Build Extension:** Verify .dxt file creates successfully
2. **Install in Claude:** Drag .dxt into Claude Desktop Extensions
3. **Test Tools:** Verify each tool returns expected responses
4. **Test Configuration:** Check user settings work properly
5. **Test State:** Verify persistence across sessions

### Debugging
- Use `console.error()` for debug messages (goes to stderr)
- Check Claude Desktop logs for error messages
- Test MCP protocol manually if needed

## SUCCESS CRITERIA

✅ Extension builds without errors  
✅ No dependency-related failures  
✅ All tools return proper JSON responses  
✅ User configuration works correctly  
✅ State persists across sessions  
✅ Files created directly in specified location  
✅ Manual build process completes successfully  

## FINAL NOTES

- **Focus on standalone implementation** - this prevents 90% of common issues
- **Use direct filesystem access** - more reliable than artifact creation
- **Ask before implementing** - prevents wasted effort on wrong assumptions
- **Test thoroughly** - build and install the extension to verify it works

This framework should be used as the foundation for any DXT extension development, with specific functionality details added based on the particular extension requirements.