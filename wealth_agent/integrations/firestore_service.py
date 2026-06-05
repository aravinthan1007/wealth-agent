"""
Tier 4: Firestore Integration
Store user profiles, goals, and memories in Google Cloud Firestore
Single source of truth for multi-user, multi-session data
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import json

# Lazy import to handle when not in GCP environment
_firestore_client = None

def get_firestore():
    """Lazy-load Firestore client (only when GCP is configured)"""
    global _firestore_client
    if _firestore_client is None:
        try:
            from google.cloud import firestore
            gcp_project = os.getenv("GCP_PROJECT_ID")
            if gcp_project:
                _firestore_client = firestore.Client(project=gcp_project)
                print(f"[OK] Firestore initialized for project {gcp_project}")
            else:
                print("[WARN] GCP_PROJECT_ID not set - Firestore disabled (using JSON fallback)")
                return None
        except ImportError:
            print("[WARN] google-cloud-firestore not installed - using JSON fallback")
            return None
    return _firestore_client

# Fallback: JSON-based storage for local development
JSON_DATA_DIR = "wealth_agent/data/firestore_backup"

def ensure_json_dir():
    """Ensure JSON backup directory exists"""
    import os
    os.makedirs(JSON_DATA_DIR, exist_ok=True)

def store_user_profile(user_id: str, profile: Dict[str, Any]) -> bool:
    """
    Store or update user profile in Firestore

    Args:
        user_id: Unique user identifier
        profile: User profile data

    Returns:
        True if successful, False otherwise
    """
    db = get_firestore()

    profile_with_ts = {
        **profile,
        "updated_at": datetime.now().isoformat(),
        "user_id": user_id
    }

    try:
        if db:
            # Store in Firestore
            db.collection("users").document(user_id).collection("profile").document("current").set(
                profile_with_ts
            )
            print(f"[OK] Profile stored for user {user_id} in Firestore")
        else:
            # Fallback to JSON
            ensure_json_dir()
            profile_file = f"{JSON_DATA_DIR}/{user_id}_profile.json"
            with open(profile_file, 'w') as f:
                json.dump(profile_with_ts, f, indent=2)
            print(f"[OK] Profile stored for user {user_id} (JSON fallback)")

        return True
    except Exception as e:
        print(f"[ERROR] Failed to store profile: {e}")
        return False

def load_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Load user profile from Firestore or JSON backup

    Args:
        user_id: Unique user identifier

    Returns:
        User profile dict or None if not found
    """
    db = get_firestore()

    try:
        if db:
            # Load from Firestore
            doc = db.collection("users").document(user_id).collection("profile").document("current").get()
            if doc.exists:
                return doc.to_dict()
        else:
            # Fallback to JSON
            profile_file = f"{JSON_DATA_DIR}/{user_id}_profile.json"
            if os.path.exists(profile_file):
                with open(profile_file, 'r') as f:
                    return json.load(f)

        return None
    except Exception as e:
        print(f"[ERROR] Failed to load profile: {e}")
        return None

def store_user_goals(user_id: str, goals: List[Dict[str, Any]]) -> bool:
    """
    Store user's goals in Firestore

    Args:
        user_id: Unique user identifier
        goals: List of Goal objects (as dicts)

    Returns:
        True if successful, False otherwise
    """
    db = get_firestore()

    try:
        if db:
            # Clear existing goals
            existing = db.collection("users").document(user_id).collection("goals").stream()
            for doc in existing:
                doc.reference.delete()

            # Store new goals
            for goal in goals:
                goal_id = goal.get("id", f"goal-{datetime.now().timestamp()}")
                goal_with_ts = {
                    **goal,
                    "updated_at": datetime.now().isoformat()
                }
                db.collection("users").document(user_id).collection("goals").document(goal_id).set(
                    goal_with_ts
                )

            print(f"[OK] Stored {len(goals)} goals for user {user_id}")
        else:
            # Fallback to JSON
            ensure_json_dir()
            goals_file = f"{JSON_DATA_DIR}/{user_id}_goals.json"
            with open(goals_file, 'w') as f:
                json.dump(goals, f, indent=2)
            print(f"[OK] Stored {len(goals)} goals (JSON fallback)")

        return True
    except Exception as e:
        print(f"[ERROR] Failed to store goals: {e}")
        return False

def load_user_goals(user_id: str) -> List[Dict[str, Any]]:
    """
    Load user's goals from Firestore

    Args:
        user_id: Unique user identifier

    Returns:
        List of goal dicts
    """
    db = get_firestore()

    try:
        if db:
            # Load from Firestore
            goals_collection = db.collection("users").document(user_id).collection("goals")
            goals = []
            for doc in goals_collection.stream():
                goals.append(doc.to_dict())
            return goals
        else:
            # Fallback to JSON
            goals_file = f"{JSON_DATA_DIR}/{user_id}_goals.json"
            if os.path.exists(goals_file):
                with open(goals_file, 'r') as f:
                    return json.load(f)

        return []
    except Exception as e:
        print(f"[ERROR] Failed to load goals: {e}")
        return []

def update_goal_progress(user_id: str, goal_id: str, progress: Dict[str, Any]) -> bool:
    """
    Update progress for a specific goal

    Args:
        user_id: Unique user identifier
        goal_id: Goal identifier
        progress: Progress data (current_amount, status, notes, etc.)

    Returns:
        True if successful, False otherwise
    """
    db = get_firestore()

    try:
        if db:
            db.collection("users").document(user_id).collection("goals").document(goal_id).update({
                "progress": progress,
                "updated_at": datetime.now().isoformat()
            })
            print(f"[OK] Updated progress for goal {goal_id}")
        # JSON fallback: update entire goals list
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update goal progress: {e}")
        return False

def store_session_memory(user_id: str, session_id: str, facts: List[Dict[str, Any]]) -> bool:
    """
    Store session facts to Memory Bank and Firestore for persistence

    Args:
        user_id: Unique user identifier
        session_id: Session identifier
        facts: List of facts to remember

    Returns:
        True if successful, False otherwise
    """
    db = get_firestore()

    session_data = {
        "user_id": user_id,
        "session_id": session_id,
        "facts": facts,
        "created_at": datetime.now().isoformat()
    }

    try:
        if db:
            db.collection("users").document(user_id).collection("sessions").document(session_id).set(
                session_data
            )
            print(f"[OK] Session {session_id} stored for user {user_id}")
        else:
            ensure_json_dir()
            session_file = f"{JSON_DATA_DIR}/{user_id}_session_{session_id}.json"
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)

        return True
    except Exception as e:
        print(f"[ERROR] Failed to store session memory: {e}")
        return False

def load_recent_sessions(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Load recent sessions for a user (for context in next session)

    Args:
        user_id: Unique user identifier
        limit: Maximum sessions to retrieve

    Returns:
        List of session dicts
    """
    db = get_firestore()

    try:
        if db:
            sessions_ref = db.collection("users").document(user_id).collection("sessions")
            sessions = []
            for doc in sessions_ref.order_by("created_at", direction="DESCENDING").limit(limit).stream():
                sessions.append(doc.to_dict())
            return sessions
        else:
            # JSON fallback: scan for session files
            import glob
            session_files = glob.glob(f"{JSON_DATA_DIR}/{user_id}_session_*.json")
            sessions = []
            for file in session_files[-limit:]:
                with open(file, 'r') as f:
                    sessions.append(json.load(f))
            return sessions

        return []
    except Exception as e:
        print(f"[ERROR] Failed to load sessions: {e}")
        return []

def get_user_context(user_id: str) -> Dict[str, Any]:
    """
    Get complete user context: profile + goals + recent sessions
    Used for Memory Bank preloading and goal agent instantiation

    Args:
        user_id: Unique user identifier

    Returns:
        Dict with profile, goals, recent_sessions
    """
    profile = load_user_profile(user_id) or {}
    goals = load_user_goals(user_id) or []
    sessions = load_recent_sessions(user_id, limit=3)

    return {
        "user_id": user_id,
        "profile": profile,
        "goals": goals,
        "recent_sessions": sessions,
        "loaded_at": datetime.now().isoformat()
    }
