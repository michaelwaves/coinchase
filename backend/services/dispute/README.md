# Dispute Service

AI-powered dispute analysis service using Claude Agent SDK and FastAPI.

## Features

- **FastAPI Backend**: Modern, fast web framework with automatic API documentation
- **Claude Agent SDK Integration**: Leverage Claude's AI capabilities for dispute analysis
- **Custom MCP Tools**: Built-in tools for dispute pattern analysis and risk calculation
- **Scalable Architecture**: Organized into routers, services, tools, and models
- **Docker Support**: Easy deployment with Docker and docker-compose
- **Dependency Injection**: Clean architecture with FastAPI dependencies

## Project Structure

```
dispute/
├── main.py                      # FastAPI application entry point
├── config.py                    # Configuration and settings
├── dependencies.py              # FastAPI dependency functions
├── models/
│   └── schemas.py              # Pydantic models for request/response
├── routers/
│   └── claude.py               # Claude Agent API routes
├── services/
│   └── claude_service.py       # Claude Agent SDK service layer
├── tools/
│   └── dispute_tools.py        # Custom MCP tools for disputes
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker compose configuration
└── .env                        # Environment variables (create from .env.example)
```

## Prerequisites

- Python 3.11+
- Node.js (for Claude Code)
- Docker and Docker Compose (for containerized deployment)
- Anthropic API Key

## Setup

### 1. Environment Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```env
ANTHROPIC_API_KEY=your_actual_api_key_here
```

### 2. Local Development

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Claude Code (required for claude-agent-sdk):

```bash
npm install -g @anthropic-ai/claude-code
```

Run the application:

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Docker Deployment

Build and run with docker-compose:

```bash
docker-compose up --build
```

Run in detached mode:

```bash
docker-compose up -d
```

Stop the service:

```bash
docker-compose down
```

## API Endpoints

### Health Check

```http
GET /
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "Dispute Service",
  "version": "1.0.0"
}
```

### Analyze Dispute

```http
POST /claude/analyze-dispute
Content-Type: application/json

{
  "dispute_description": "Customer claims unauthorized charge on their card",
  "transaction_id": "TXN123456",
  "amount": 299.99
}
```

Response:
```json
{
  "analysis": "Detailed analysis from Claude...",
  "transaction_id": "TXN123456",
  "status": "completed"
}
```

### Simple Query

```http
POST /claude/query?prompt=What are common types of disputes?
```

Response:
```json
{
  "prompt": "What are common types of disputes?",
  "response": "Claude's response...",
  "status": "success"
}
```

## API Documentation

Once the service is running, access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Custom MCP Tools

The service includes custom in-process MCP tools:

1. **analyze_dispute_pattern**: Analyzes disputes for common patterns (fraud, quality issues, delivery problems, refunds)
2. **calculate_dispute_risk**: Calculates risk score based on amount and customer history

These tools are automatically available to Claude during dispute analysis.

## Architecture

### Dependency Injection Flow

```
Request → Router → Dependencies → Service → Claude Agent SDK
                      ↓
                  Config/Settings
```

### Component Responsibilities

- **Routers**: Handle HTTP requests and responses
- **Services**: Business logic and Claude Agent SDK interactions
- **Tools**: Custom MCP tools for Claude
- **Dependencies**: Shared logic and resource management
- **Models**: Request/response validation with Pydantic
- **Config**: Centralized configuration management

## Development

### Adding New Endpoints

1. Create route handler in `routers/`
2. Add business logic in `services/`
3. Define request/response models in `models/schemas.py`
4. Register router in `main.py`

### Adding Custom Tools

1. Define tool function in `tools/` with `@tool` decorator
2. Add to MCP server in `create_dispute_tools_server()`
3. Tools are automatically available to Claude

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| ANTHROPIC_API_KEY | Anthropic API key (required) | - |
| APP_NAME | Application name | Dispute Service |
| APP_VERSION | Application version | 1.0.0 |
| DEBUG | Debug mode | false |
| MAX_TURNS | Max Claude conversation turns | 5 |
| ALLOWED_TOOLS | Allowed Claude tools | ["Read", "Write", "Bash"] |

## License

MIT

