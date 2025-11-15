# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Setup Environment

```bash
# Run the setup script (recommended)
./setup.sh

# Or manually:
cp ENV_TEMPLATE .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Step 2: Start the Service

**Option A: Local Development**
```bash
source venv/bin/activate
python main.py
```

**Option B: Docker (Recommended)**
```bash
docker-compose up --build
```

### Step 3: Test the API

**Access Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Run Tests:**
```bash
python test_api.py
```

---

## 📋 Example API Calls

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Dispute Service",
  "version": "1.0.0"
}
```

### 2. Simple Query (Basic Claude Integration)

```bash
curl -X POST "http://localhost:8000/claude/query?prompt=What+is+2+plus+2?" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "prompt": "What is 2 plus 2?",
  "response": "2 plus 2 equals 4.",
  "status": "success"
}
```

### 3. Analyze Dispute (Advanced - Uses Custom MCP Tools)

```bash
curl -X POST "http://localhost:8000/claude/analyze-dispute" \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "Customer claims unauthorized charge on their credit card for $299.99. They state they never made this purchase and want a full refund immediately.",
    "transaction_id": "TXN-2025-11-15-001",
    "amount": 299.99
  }'
```

**Response:**
```json
{
  "analysis": "Detailed analysis including pattern detection, risk assessment, and recommendations...",
  "transaction_id": "TXN-2025-11-15-001",
  "status": "completed"
}
```

---

## 🧰 What's Included

### Custom MCP Tools

The service includes 2 custom in-process MCP tools that Claude can use:

1. **`analyze_dispute_pattern`** - Detects patterns like fraud, quality issues, delivery problems
2. **`calculate_dispute_risk`** - Calculates risk score based on amount and customer history

These tools are automatically available to Claude during dispute analysis without any external server setup!

### Scalable Architecture

```
dispute/
├── main.py              # FastAPI app entry point
├── config.py            # Settings management
├── dependencies.py      # FastAPI dependencies
├── models/
│   └── schemas.py      # Request/response models
├── routers/
│   └── claude.py       # API endpoints
├── services/
│   └── claude_service.py  # Business logic
└── tools/
    └── dispute_tools.py   # Custom MCP tools
```

---

## 🔧 Configuration

Edit `.env` file:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional
MAX_TURNS=5
ALLOWED_TOOLS=["Read", "Write", "Bash"]
DEBUG=false
```

---

## 🐳 Docker Commands

```bash
# Build and start
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild after code changes
docker-compose up --build --force-recreate
```

---

## 🧪 Testing

### Automated Test Script

```bash
python test_api.py
```

### Manual Testing with curl

**Test 1: Health**
```bash
curl http://localhost:8000/health
```

**Test 2: Simple Question**
```bash
curl -X POST "http://localhost:8000/claude/query?prompt=Explain+dispute+resolution" 
```

**Test 3: Fraud Dispute Analysis**
```bash
curl -X POST "http://localhost:8000/claude/analyze-dispute" \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_description": "Fraudulent transaction - card was stolen",
    "amount": 1500.00
  }'
```

---

## 📚 Key Features

✅ **FastAPI** - Modern, fast web framework with automatic API docs  
✅ **Claude Agent SDK** - Latest version (0.1.6) with full support  
✅ **Custom MCP Tools** - In-process tools, no external servers needed  
✅ **Dependency Injection** - Clean, testable architecture  
✅ **Docker Support** - Easy deployment with compose  
✅ **Type Safety** - Pydantic models for validation  
✅ **Scalable Structure** - Organized by routers, services, tools  

---

## 🆘 Troubleshooting

**Issue: "Anthropic API key not configured"**
- Make sure `.env` file exists and contains `ANTHROPIC_API_KEY`
- Check that the API key is valid

**Issue: "Claude Code not found"**
- Install Node.js first: https://nodejs.org/
- Run: `npm install -g @anthropic-ai/claude-code`

**Issue: "Module not found"**
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**Issue: Docker build fails**
- Make sure Docker is running
- Try: `docker-compose down && docker-compose up --build`

---

## 📖 Next Steps

1. **Customize Tools**: Add more dispute analysis tools in `tools/dispute_tools.py`
2. **Add Endpoints**: Create new routers in `routers/` directory
3. **Enhance Analysis**: Improve dispute patterns in `services/claude_service.py`
4. **Add Database**: Integrate PostgreSQL or MongoDB for dispute storage
5. **Add Authentication**: Implement JWT or OAuth2 authentication

---

## 📞 Support

- API Documentation: http://localhost:8000/docs
- Claude Agent SDK: https://github.com/anthropics/claude-agent-sdk-python
- FastAPI Docs: https://fastapi.tiangolo.com/

Happy coding! 🎉

