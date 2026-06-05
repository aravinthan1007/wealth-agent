"""Frontend API Server - Connects Aurelius UI to ADK Agents.

Serves the Omni-Asset Ledger frontend and provides REST API endpoints
that call the Aurelius agent and sub-agents to fetch wealth data and insights.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, Response
from flask_cors import CORS
import sys
from pathlib import Path
import json
import asyncio
from datetime import datetime, timedelta
import os
import time
import uuid

# Add parent directory to path for agent imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from wealth_agent import root_agent
from wealth_agent import user_data as user_data_module
from wealth_agent.tools.finance import (
    get_networth, get_expenses, get_credit_cards, get_income, get_profile, get_accounts
)
from wealth_agent.tools.market import get_stock_quotes
from wealth_agent.tools.traces import query_traces

app = Flask(__name__, static_folder='.')
CORS(app)

# User data storage file
USER_DATA_FILE = Path(__file__).parent / '.user_data.json'
PROGRESS_DATA_FILE = Path(__file__).parent / '.progress_data.json'

def load_user_data():
    """Load user onboarding data if exists."""
    if USER_DATA_FILE.exists():
        try:
            with open(USER_DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def save_user_data(data):
    """Save user onboarding data."""
    try:
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False

def load_progress_data():
    """Load progress data."""
    if PROGRESS_DATA_FILE.exists():
        try:
            with open(PROGRESS_DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def save_progress_data(data):
    """Save progress data."""
    try:
        with open(PROGRESS_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False

# Mock data (in production, this would come from agents)
MOCK_LIQUID_ASSETS = [
    {"name": "Global Equities", "description": "Managed Portfolio", "icon": "account_balance", "value": 42500000, "change": 1.2},
    {"name": "Fixed Income", "description": "Municipal Bonds", "icon": "description", "value": 28100000, "change": 0.0},
    {"name": "Cash & Equivalents", "description": "Multiple Currencies", "icon": "payments", "value": 13600000, "change": -0.1},
]

MOCK_TANGIBLE_ASSETS = [
    {
        "id": "asset1",
        "type": "Real Estate",
        "name": "Châlet Les Bassets",
        "location": "Gstaad, Switzerland",
        "acquisition": 12500000,
        "currentValue": 18200000,
        "image": "https://lh3.googleusercontent.com/aida-public/AB6AXuCzkZ2xCCzI_iCqLKjqofAzHjLDKaEHsMpkazES5D4hycOgyV07NcLr6d5BUtHINGcMB_mwKDaI821e1MSjC1HHUbk656P2SkqcQZZ9QBEnwar1rzRuV9qlxrxhiAJrGZbxEiWbRE7_hvGMcz6siU1j4rbNLPO5YVlZrtFot734ykh4qtE_CAhRnf1QclDN0ech77BMgsNnDyaDsaR4F5q8tb37M-gpB_tfVbBwXFukBdnocJCVUe9V9aVjGEznCmSuGTt4L6M9Bg"
    },
    {
        "id": "asset2",
        "type": "Classic Automotive",
        "name": "1962 Ferrari 250 GTO",
        "location": "Chassis 3413",
        "acquisition": 38000000,
        "currentValue": 42500000,
        "image": "https://lh3.googleusercontent.com/aida-public/AB6AXuA4JHmerMD443wYUn3iW39lVwvOsewf2qHp-H7tM21eG4afTq9p4hqnEgXzXaesoJuVi0Uia6sFSIxO1nO-Rmj8qtqJ0IEHfhj_JgpG6M7aWDsDAiQ4p8TGiImCDNgmlO0Aif-kGVpUtU2kMHee05m3fbfzl_HGFzsxvIUbZbRTaklQoaI1RSkhD7k3Ouu6aOmn55UTlJpupql8_f6xWrxfqGRfMj99Qf4517xQgsD9u2ZYxsFBs3MeC9W6H_1ZRf7WolIbXygeuw"
    },
]

MOCK_LIABILITIES = [
    {"name": "Mortgage: London Townhouse", "dueDate": "Due: Oct 15, 2023", "amount": 5800000, "icon": "real_estate_agent", "urgent": False},
    {"name": "Centurion Card Balance", "dueDate": "Due in 3 Days", "amount": 350000, "icon": "credit_score", "urgent": True},
]

# Routes

@app.route('/')
def index():
    """Serve dashboard or redirect to onboarding."""
    user_data = load_user_data()
    if not user_data:
        return redirect('/onboard')
    return send_from_directory('.', 'index.html')

@app.route('/onboard')
def onboard():
    """Serve the onboarding form."""
    user_data = load_user_data()
    if user_data:
        return redirect('/')
    return send_from_directory('.', 'onboarding.html')

@app.route('/ledger')
def aurelius_ledger():
    """Serve the Aurelius Wealth Ledger UI."""
    ledger_path = Path(__file__).parent.parent / 'aurelius_ledger.html'
    if ledger_path.exists():
        with open(ledger_path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    return jsonify({"error": "Ledger HTML not found"}), 404

@app.route('/api/user', methods=['GET'])
def get_user():
    """Check if user is onboarded."""
    user_data = load_user_data()
    return jsonify({
        "onboarded": user_data is not None,
        "user": user_data
    })

@app.route('/api/onboard', methods=['POST'])
def onboard_user():
    """Save user onboarding data to both .user_data.json and user_data store.

    Request JSON:
    - fullName: User's full name
    - residency: Country of residence
    - citizenship: Citizenship country
    - netWorth: Net worth in USD
    - liquidAssets: Liquid assets in USD
    - liabilities: Liabilities in USD
    - investmentExperience: Level of investment experience
    - investmentObjective: Investment objectives
    - timeHorizon: Investment time horizon
    - riskTolerance: Risk tolerance level
    - assets (optional): Dict of asset categories and values
    - expenses (optional): List of expense records
    - income (optional): List of income sources
    - credit_cards (optional): List of credit card info
    """
    try:
        data = request.json
        # Validate required fields for basic onboarding
        required_fields = ['fullName', 'residency', 'citizenship', 'netWorth',
                          'liquidAssets', 'liabilities', 'investmentExperience',
                          'investmentObjective', 'timeHorizon', 'riskTolerance']

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        # Add timestamp and generate user_id
        data['onboarded_at'] = datetime.now().isoformat()
        user_id = data.get('user_id') or 'user_' + str(int(datetime.now().timestamp()))

        # Save to legacy .user_data.json file
        if not save_user_data(data):
            return jsonify({"error": "Failed to save user data"}), 500

        # Also save to user_data store with full financial profile
        user_data_store = {
            "assets": data.get("assets", {
                "liquid": float(data.get("liquidAssets", 0)),
                "other": 0
            }),
            "liabilities": {"total": float(data.get("liabilities", 0))},
            "expenses": data.get("expenses", []),
            "income": data.get("income", []),
            "credit_cards": data.get("credit_cards", []),
            "profile": {
                "risk_tolerance": data.get("riskTolerance", "moderate"),
                "retirement_age": data.get("retirementAge", 65),
                "goals": data.get("goals", []),
                "investment_objective": data.get("investmentObjective", ""),
                "time_horizon": data.get("timeHorizon", ""),
                "full_name": data.get("fullName", ""),
                "residency": data.get("residency", ""),
                "citizenship": data.get("citizenship", ""),
            }
        }

        if not user_data_module.save_user_data(user_id, user_data_store):
            # If saving to store fails, still succeed but log warning
            print(f"[WARN] Failed to save {user_id} to user_data store")

        return jsonify({
            "success": True,
            "message": "Onboarding completed successfully",
            "user_id": user_id,
            "user": data
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/save-progress', methods=['POST'])
def save_progress():
    """Save onboarding progress."""
    try:
        data = request.json
        progress = {
            "step": data.get('step', 1),
            "data": data.get('data', {}),
            "saved_at": datetime.now().isoformat()
        }

        if save_progress_data(progress):
            return jsonify({
                "success": True,
                "message": "Progress saved"
            }), 200
        else:
            return jsonify({"error": "Failed to save progress"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wealth', methods=['GET'])
def get_wealth():
    """Get total net worth from Aurelius agent."""
    try:
        # Call agent tool directly
        networth = get_networth()
        return jsonify({
            "networth": networth,
            "currency": "USD",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/liquid-assets', methods=['GET'])
def get_liquid_assets_data():
    """Get liquid assets breakdown."""
    try:
        total = sum(asset['value'] for asset in MOCK_LIQUID_ASSETS)
        return jsonify({
            "assets": MOCK_LIQUID_ASSETS,
            "total": total
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tangible-assets', methods=['GET'])
def get_tangible_assets_data():
    """Get tangible assets (real estate, collectibles, etc.)."""
    try:
        total = sum(asset['currentValue'] for asset in MOCK_TANGIBLE_ASSETS)
        return jsonify({
            "assets": MOCK_TANGIBLE_ASSETS,
            "total": total
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/liabilities', methods=['GET'])
def get_liabilities_data():
    """Get liabilities breakdown."""
    try:
        total = sum(liability['amount'] for liability in MOCK_LIABILITIES)
        return jsonify({
            "liabilities": MOCK_LIABILITIES,
            "total": total
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/insights', methods=['GET'])
def get_insights_data():
    """Get AI-generated insights from Aurelius."""
    try:
        insights = [
            {
                "title": "Portfolio Strategy",
                "message": "Recommended rotation: Reduce exposure in European Equities (-2%) to allocate towards emerging market fixed income.",
                "isAlert": True,
                "action": "Review Proposal",
                "actionType": "review_proposal",
                "actionData": json.dumps({
                    "title": "Portfolio Rebalancing Proposal",
                    "description": "Markets Steward recommends a strategic rotation in your portfolio.",
                    "details": "<ul class='list-disc list-inside'><li>Reduce European Equities by 2%</li><li>Increase Emerging Market Fixed Income by 2%</li><li>Maintains overall risk profile</li></ul>"
                })
            },
            {
                "title": "Concierge Alert",
                "message": "Scheduled maintenance for Châlet Les Bassets HVAC system requires approval.",
                "isAlert": False,
                "action": None,
                "actionType": None,
                "actionData": None
            },
            {
                "title": "Liability Management",
                "message": "Q3 Property Tax for London Townhouse (£145,000) will be automatically debited in 4 days.",
                "isAlert": False,
                "action": None,
                "actionType": None,
                "actionData": None
            },
            {
                "title": "Market Intelligence",
                "message": "Your portfolio shows strong fundamentals. Consider your upcoming tax planning session this quarter.",
                "isAlert": False,
                "action": None,
                "actionType": None,
                "actionData": None
            }
        ]

        # Try to get real insights from Aurelius
        try:
            if root_agent:
                # Could call agent here for dynamic insights
                pass
        except:
            pass

        return jsonify({"insights": insights})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/networth/<user_id>', methods=['GET'])
def get_user_networth(user_id: str):
    """Get net worth for a specific user from user_data store."""
    try:
        networth = get_networth(user_id=user_id)
        return jsonify({
            "user_id": user_id,
            "networth": networth,
            "currency": "USD",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/accounts/<user_id>', methods=['GET'])
def get_user_accounts(user_id: str):
    """Get accounts for a specific user from user_data store."""
    try:
        accounts = get_accounts(user_id=user_id)
        return jsonify({
            "user_id": user_id,
            "accounts": accounts,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/expenses/<user_id>', methods=['GET'])
def get_user_expenses(user_id: str):
    """Get expenses for a specific user from user_data store.

    Query params:
    - month (YYYY-MM): Filter to specific month
    """
    try:
        month = request.args.get('month', None)
        expenses = get_expenses(user_id=user_id, month=month)
        return jsonify({
            "user_id": user_id,
            "month": month,
            "expenses": expenses,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/income/<user_id>', methods=['GET'])
def get_user_income(user_id: str):
    """Get income for a specific user from user_data store."""
    try:
        income_data = get_income(user_id=user_id)
        return jsonify({
            "user_id": user_id,
            "income": income_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/credit-cards/<user_id>', methods=['GET'])
def get_user_credit_cards(user_id: str):
    """Get credit cards for a specific user from user_data store."""
    try:
        cards = get_credit_cards(user_id=user_id)
        return jsonify({
            "user_id": user_id,
            "credit_cards": cards,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat with Aurelius agent about wealth questions."""
    try:
        data = request.json
        message = data.get('message', '')

        if not message:
            return jsonify({"error": "No message provided"}), 400

        # Route to appropriate agent based on message keywords
        response = route_to_agent(message)

        return jsonify({
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get past agent queries and traces."""
    try:
        if root_agent:
            traces = query_traces(limit=10)
            return jsonify(traces)
        return jsonify({"traces": [], "count": 0})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/run_sse', methods=['POST'])
def run_sse():
    """Stream agent response with trace + provenance (Tier 2).

    Endpoint for Agent Insights rendering. Streams:
    1. Agent response chunks
    2. Final trace info
    3. Provenance footer data

    Request JSON:
    - message (str): Query to process
    - user_id (str, optional): User identifier for data store
    - trace_limit (int, optional): Number of traces to include
    """
    try:
        data = request.json or {}
        message = data.get('message', '')
        user_id = data.get('user_id', None)
        trace_limit = data.get('trace_limit', 5)

        if not message:
            return jsonify({"error": "No message provided"}), 400

        # Generate unique run ID for this execution
        run_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        def generate():
            """Generator for SSE stream."""
            # Stream 1: Agent response
            yield f'data: {json.dumps({"type": "response", "content": "Agent processing: " + message})}\n\n'

            # Get actual agent response
            try:
                response = route_to_agent(message, user_id)
                yield f'data: {json.dumps({"type": "response", "content": response})}\n\n'
            except Exception as e:
                yield f'data: {json.dumps({"type": "error", "content": str(e)})}\n\n'
                return

            # Stream 2: Trace info
            try:
                traces = query_traces(limit=trace_limit)
                latency_ms = int((time.time() - start_time) * 1000)

                # Add this run to traces
                current_trace = {
                    "trace_id": f"trace-{run_id}",
                    "agent": "aurelius",
                    "tool": "route_to_agent",
                    "input": message,
                    "output": response[:100] + "..." if len(response) > 100 else response,
                    "latency_ms": latency_ms,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "faithfulness_score": 0.92,  # Mock score
                }

                yield f'data: {json.dumps({"type": "trace", "content": current_trace})}\n\n'

                # Stream 3: Provenance footer
                provenance = {
                    "steps": traces.get("count", 0) + 1,
                    "latency_ms": latency_ms,
                    "faithfulness": current_trace["faithfulness_score"],
                    "trace_url": f"/api/trace/{run_id}",
                    "timestamp": datetime.utcnow().isoformat(),
                }

                yield f'data: {json.dumps({"type": "provenance", "content": provenance})}\n\n'

            except Exception as e:
                yield f'data: {json.dumps({"type": "error", "content": "Trace error: " + str(e)})}\n\n'

            # Signal completion
            yield f'data: {json.dumps({"type": "complete", "content": "Done"})}\n\n'

        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/trace/<trace_id>', methods=['GET'])
def get_trace(trace_id: str):
    """Get detailed trace data for a run (supports /run_sse)."""
    try:
        traces = query_traces(limit=100)
        for trace in traces.get("traces", []):
            if trace.get("trace_id") == f"trace-{trace_id}":
                return jsonify(trace)
        return jsonify({"error": "Trace not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Helper Functions

def route_to_agent(message: str, user_id: str = None) -> str:
    """Route message to appropriate agent and get response.

    Args:
        message: Query to process
        user_id: Optional user identifier for data store
    """
    message_lower = message.lower()

    # Keyword-based routing
    if any(word in message_lower for word in ['stock', 'market', 'quote', 'rebalance', 'portfolio']):
        return handle_markets_query(message, user_id)
    elif any(word in message_lower for word in ['account', 'asset', 'income', 'credit', 'liability']):
        return handle_estate_query(message, user_id)
    elif any(word in message_lower for word in ['book', 'schedule', 'concierge', 'service', 'maintenance']):
        return handle_concierge_query(message, user_id)
    else:
        return handle_general_query(message, user_id)

def handle_general_query(message: str, user_id: str = None) -> str:
    """Handle general wealth questions via Aurelius."""
    keywords = {
        "net worth": lambda: f"Your net worth is ${get_networth(user_id=user_id):,.0f}",
        "income": lambda: f"Your monthly income is ${get_income(user_id=user_id).get('total_monthly', 0):,.0f}",
        "expenses": lambda: f"Your monthly expenses are ${get_expenses(user_id=user_id):,.0f}",
        "profile": lambda: "Here's your profile information...",
        "credit": lambda: f"You have {len(get_credit_cards(user_id=user_id))} credit cards on file",
    }

    for keyword, handler in keywords.items():
        if keyword in message.lower():
            try:
                return handler()
            except:
                pass

    return "I can help you analyze your wealth. Try asking about your net worth, income, expenses, or credit cards."

def handle_markets_query(message: str, user_id: str = None) -> str:
    """Route to Markets Steward."""
    if 'rebalance' in message.lower():
        return "Markets Steward suggests a strategic rebalancing. Would you like to review the proposal?"
    elif 'quote' in message.lower() or 'price' in message.lower():
        quotes = get_stock_quotes(['AAPL', 'GOOGL'])
        return f"Current quotes: AAPL ${quotes['AAPL']['price']:.2f}, GOOGL ${quotes['GOOGL']['price']:.2f}"
    return "Markets Steward is ready to help with portfolio analysis and rebalancing."

def handle_estate_query(message: str, user_id: str = None) -> str:
    """Route to Estate Steward."""
    return "Estate Steward is reviewing your assets and liabilities. What would you like to know about your accounts or income?"

def handle_concierge_query(message: str, user_id: str = None) -> str:
    """Route to Concierge Steward."""
    return "Concierge Steward can help arrange services and maintenance. What do you need?"

if __name__ == '__main__':
    print("[*] Starting Aurelius Wealth Frontend Server...")
    print("[*] Open http://localhost:5000 in your browser")
    print("[*] Connected to Aurelius Agent System")

    if root_agent:
        print(f"[OK] Agent: {root_agent.name}")
        print(f"[OK] Model: {root_agent.model}")
        print(f"[OK] Tools: {len(root_agent.tools)}")
    else:
        print("[WARN] Agent not initialized - using mock data only")

    app.run(debug=True, port=5000, use_reloader=False)
