# Aurelius Wealth - Omni-Asset Ledger Frontend

Beautiful, modern wealth management UI connected to the Aurelius AI agent system.

## Features

- **Omni-Asset Ledger Dashboard**: View all assets, liabilities, and wealth metrics at a glance
- **Liquid Assets Table**: Track stocks, bonds, cash by category with real-time changes
- **Tangible Wealth Cards**: Beautiful display of real estate, collectibles, and other tangible assets
- **Liabilities Overview**: Monitor mortgages and credit obligations
- **Agent Insights Sidebar**: AI-generated insights and action items from Aurelius
- **Chat Interface**: Talk directly with Aurelius about your wealth
- **Review Proposals**: Accept/decline rebalancing and service booking proposals

## Architecture

```
Frontend (HTML/Tailwind CSS) ← Flask API Server ← Aurelius Agent System
├─ index.html (beautiful UI)
├─ app.py (REST API endpoints)
└─ assets (images, styling)
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Frontend Server

```bash
python frontend/app.py
```

Output:
```
🚀 Starting Aurelius Wealth Frontend Server...
📊 Open http://localhost:5000 in your browser
🤖 Connected to Aurelius Agent System
✓ Agent: Aurelius
✓ Model: gemini-3.1-flash-lite
✓ Tools: 9
```

### 3. Open in Browser

Visit: **http://localhost:5000**

## API Endpoints

The Flask server provides these REST endpoints for the frontend:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/wealth` | GET | Total net worth |
| `/api/liquid-assets` | GET | Stocks, bonds, cash breakdown |
| `/api/tangible-assets` | GET | Real estate, collectibles, etc. |
| `/api/liabilities` | GET | Mortgages, credit card balances |
| `/api/insights` | GET | AI-generated insights from Aurelius |
| `/api/chat` | POST | Chat with Aurelius agent |
| `/api/history` | GET | Past queries and traces |

## How It Works

### Data Flow

1. **Frontend loads** → Calls `/api/wealth`, `/api/liquid-assets`, etc.
2. **API server** fetches data from Aurelius agent tools
3. **Tools return** data (real or mock)
4. **Frontend renders** beautiful UI with live data
5. **User interacts** → Modal opens for chat or proposals
6. **Chat message** → POST to `/api/chat`
7. **Agent responds** → Routes to appropriate sub-agent
8. **Response** rendered in UI

### Example: "What's my net worth?"

```
User → Frontend → /api/chat → Flask → route_to_agent() → 
handle_general_query() → get_networth() → 
"Your net worth is $142,850,000" → Frontend displays
```

### Example: "Rebalance to 60/40"

```
User → Frontend → /api/chat → Flask → route_to_agent() → 
handle_markets_query() → Markets Steward → propose_rebalance() → 
Returns proposal with requires_confirmation=true → 
Modal displays for approval
```

## Customization

### Change Styling

Edit `index.html` Tailwind config in `<script id="tailwind-config">`:

```javascript
"colors": {
    "primary": "#061b0e",
    "secondary": "#775a19",
    // ... customize color palette
}
```

### Add New Data

Edit `frontend/app.py`:

1. Add new endpoint (e.g., `/api/tax-planning`)
2. Add route handler
3. Return JSON data
4. Call from frontend JavaScript

### Connect Real Agent Data

Replace mock data in `app.py` with live agent calls:

```python
@app.route('/api/custom-endpoint', methods=['GET'])
def my_endpoint():
    # Instead of MOCK_DATA, call your agent:
    result = root_agent.run({"input": "your query"})
    return jsonify(result)
```

## Features in Detail

### Portfolio Section
- Displays net worth prominently
- Shows YTD growth and last sync time
- Beautiful neo-classic design

### Liquid Assets
- Table view of stocks, bonds, cash
- Real-time price changes (up/down indicators)
- Asset categories and descriptions

### Tangible Wealth
- Card-based layout
- Images of assets (real estate, vehicles)
- Acquisition price vs. current market value
- Click to view details

### Liabilities
- Clear list of obligations
- Due dates with visual urgency
- Automatic debit notices

### Agent Insights
- AI-generated recommendations
- Action buttons for proposals
- Concierge alerts
- Tax/compliance reminders

### Chat Modal
- Real-time conversation with Aurelius
- Auto-routes to appropriate sub-agent
- Proposal handling with approve/decline

## Development

### Running with ADK Agent

If ADK agent is initialized:
```bash
# Aurelius agent will be used for real data
python frontend/app.py
```

If ADK agent fails to initialize:
```bash
# Frontend still works with mock data
# See: ⚠ Agent not initialized - using mock data only
```

### Testing Endpoints

```bash
# Test wealth endpoint
curl http://localhost:5000/api/wealth

# Test chat
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my net worth?"}'
```

### Debugging

Set `debug=True` in `app.py` for:
- Auto-reload on code changes
- Detailed error messages
- Interactive debugger (POST with errors)

## Integration with ADK Agents

The frontend automatically connects to:
- **Aurelius** (coordinator) for general queries
- **Markets Steward** for portfolio/stock questions
- **Estate Steward** for asset/liability/income
- **Concierge Steward** for service bookings

Routing is automatic based on message keywords.

## Troubleshooting

### Port 5000 in Use
```bash
python frontend/app.py --port 5001
```

### Agent Not Initializing
Ensure `.env` has `GEMINI_API_KEY` set. Frontend will work with mock data if agent fails.

### CORS Errors
Flask-CORS is already configured in `app.py`.

### Missing Tailwind Classes
Frontend uses Tailwind CDN. Ensure internet connection for stylesheet loading.

## File Structure

```
frontend/
├── index.html          # Main UI (all-in-one HTML with embedded CSS/JS)
├── app.py              # Flask server + API endpoints
├── requirements.txt    # Dependencies
└── README.md           # This file
```

## Next Steps

1. **Deploy locally**: Run `python app.py`, visit http://localhost:5000
2. **Connect real agent**: Replace mock data with live agent queries
3. **Add features**: New endpoints, insights, proposals
4. **Move to production**: Docker, Cloud Run, etc. (see TIER3.md)

---

**Ready to explore your wealth with AI?** Open http://localhost:5000 🚀
