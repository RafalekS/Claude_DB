# n8n MCP Tools

Integration commands for n8n workflow management via MCP servers.

## Description

Assist with n8n workflow parsing, MCP server connections, vectorization, and database operations.

## Requirements

- n8n-templates project setup
- Three MCP servers configured:
  - n8n MCP Server
  - QDRANT MCP Server
  - Supabase MCP Server

## MCP Server Integrations

### 1. n8n MCP Server
Workflow connectivity and management:
```bash
npm run n8n-demo     # List workflows
npm run import       # Import workflows
```

### 2. QDRANT MCP Server
Semantic search capabilities:
```bash
npm run vectorize-mcp  # Vectorize workflows for similarity search
```

### 3. Supabase MCP Server
Structured storage for workflow metadata:
```bash
npm run supabase-mcp  # Query and store workflow data
```

## Core Project Files

| File | Purpose |
|------|---------|
| `workflow-parser.js` | Extract metadata from workflows |
| `vectorize-workflows.js` | Create vector embeddings |
| `n8n-mcp-client.js` | Server communication layer |
| `import-to-n8n.js` | Workflow deployment utility |
| `mcp-client-config.js` | Connection configuration |

## Capabilities

This integration enables:
- **Workflow Parsing**: Extract and analyze workflow structures
- **MCP Server Connections**: Connect to n8n, QDRANT, Supabase
- **Vectorization**: Create embeddings for semantic search
- **Database Queries**: Store and retrieve workflow metadata
- **New Integrations**: Develop additional MCP connections

## Examples

```
/n8n-mcp-tools list-workflows
/n8n-mcp-tools search "email automation"
/n8n-mcp-tools import workflow.json
/n8n-mcp-tools vectorize
```

## Important Notes

- Ensure MCP servers are running before operations
- Vector embeddings enable semantic workflow search
- Supabase stores structured metadata for querying
- Check mcp-client-config.js for connection settings

## Source

From https://github.com/kingler/n8n_agent/.claude/commands
