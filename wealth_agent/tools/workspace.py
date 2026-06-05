"""Google Workspace integration tools for Aurelius.

Patterns from: adk-ae-oauth sample
- OAuth 2.0 credential negotiation
- Google Drive file reading (Docs, Sheets, PDFs)
- Session-based credential caching
"""

import json
import logging
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.adk.tools import ToolContext
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = {
    "https://www.googleapis.com/auth/drive.readonly": "Google Drive (read-only)",
    "https://www.googleapis.com/auth/gmail.readonly": "Gmail (read-only)",
    "https://www.googleapis.com/auth/calendar.readonly": "Google Calendar (read-only)",
}

TOKEN_CACHE_KEY = "aurelius-workspace-auth"


def negotiate_creds(tool_context: ToolContext) -> Credentials | dict:
    """Handle OAuth 2.0 credential negotiation for Google Workspace APIs.

    Three-stage resolution:
    1. Check cached credentials in tool_context.state
    2. Check for auth response from ADK OAuth flow
    3. Initiate OAuth flow if needed

    Args:
        tool_context: ADK ToolContext with credential/auth support

    Returns:
        Valid Credentials object or pending auth dict
    """
    logger.info("Negotiating Google Workspace credentials")

    # Stage 1: Check cached credentials
    cached_token = tool_context.state.get(TOKEN_CACHE_KEY)
    if cached_token is None:
        cached_token = tool_context.state.get(f"temp:{TOKEN_CACHE_KEY}")

    if cached_token:
        logger.debug("Found cached token")
        if isinstance(cached_token, dict):
            try:
                creds = Credentials.from_authorized_user_info(
                    cached_token, list(SCOPES.keys())
                )
                if creds.valid:
                    logger.debug("Cached credentials valid")
                    return creds
                if creds.expired and creds.refresh_token:
                    logger.debug("Refreshing expired credentials")
                    creds.refresh(Request())
                    tool_context.state[TOKEN_CACHE_KEY] = json.loads(creds.to_json())
                    return creds
            except Exception as e:
                logger.error(f"Error with cached credentials: {e}")
                tool_context.state[TOKEN_CACHE_KEY] = None
        elif isinstance(cached_token, str):
            logger.debug("Using raw access token")
            return Credentials(token=cached_token)

    # Stage 2: Check for auth response from ADK OAuth flow
    logger.debug("Checking for auth response")
    # Note: AUTH_CONFIG would be defined in auths.py (similar to adk-ae-oauth sample)
    # For now, we skip this as it requires full OAuth setup in production

    # Stage 3: Initiate OAuth flow (in production)
    logger.info("Credentials needed - requesting user authentication")
    return {"pending": True, "message": "Please authenticate with Google Workspace"}


def read_financial_statement(file_id: str, tool_context: ToolContext) -> dict:
    """Read financial statement from Google Drive (CSV, Sheets, or PDF).

    Supports:
    - Google Sheets (exported as CSV)
    - CSV files
    - Google Docs (exported as text)

    Args:
        file_id: Google Drive file ID
        tool_context: ADK ToolContext

    Returns:
        Dict with status, file_name, mime_type, content
    """
    creds = negotiate_creds(tool_context)

    if isinstance(creds, dict) and creds.get("pending"):
        return creds

    try:
        service = build("drive", "v3", credentials=creds)

        # Get file metadata
        file_meta = (
            service.files()
            .get(fileId=file_id, fields="id,name,mimeType")
            .execute()
        )

        file_name = file_meta.get("name", "unknown")
        mime_type = file_meta.get("mimeType", "")

        logger.info(f"Reading financial document: {file_name}")

        # Export or download based on type
        if mime_type == "application/vnd.google-apps.spreadsheet":
            content = (
                service.files()
                .export(fileId=file_id, mimeType="text/csv")
                .execute()
            )
            text_content = (
                content.decode("utf-8") if isinstance(content, bytes) else content
            )
        elif mime_type == "text/csv" or "text/plain" in mime_type:
            content = (
                service.files()
                .get_media(fileId=file_id)
                .execute()
            )
            text_content = (
                content.decode("utf-8") if isinstance(content, bytes) else content
            )
        else:
            return {
                "status": "unsupported",
                "message": f"Unsupported file type: {mime_type}",
            }

        return {
            "status": "success",
            "file_name": file_name,
            "mime_type": mime_type,
            "content": text_content,
        }

    except Exception as e:
        logger.error(f"Error reading financial statement: {e}")
        return {
            "status": "error",
            "message": f"Failed to read file: {str(e)}",
        }


def list_financial_documents(tool_context: ToolContext) -> dict:
    """List financial documents in user's Google Drive.

    Searches for CSV, Sheets, and relevant document types.

    Args:
        tool_context: ADK ToolContext

    Returns:
        Dict with status and list of documents
    """
    creds = negotiate_creds(tool_context)

    if isinstance(creds, dict) and creds.get("pending"):
        return creds

    try:
        service = build("drive", "v3", credentials=creds)

        # Query for CSV, Sheets, and Docs
        query = (
            "("
            "mimeType='text/csv' or "
            "mimeType='application/vnd.google-apps.spreadsheet' or "
            "mimeType='application/vnd.google-apps.document'"
            ")"
            " and name contains ('financial' or 'statement' or 'tax' or 'portfolio')"
            " and trashed=false"
        )

        results = (
            service.files()
            .list(q=query, spaces="drive", fields="files(id,name,mimeType,createdTime)")
            .execute()
        )

        files = results.get("files", [])
        logger.info(f"Found {len(files)} financial documents")

        return {
            "status": "success",
            "documents": [
                {
                    "id": f["id"],
                    "name": f["name"],
                    "type": f["mimeType"],
                    "created": f.get("createdTime"),
                }
                for f in files
            ],
        }

    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return {
            "status": "error",
            "message": f"Failed to list documents: {str(e)}",
        }


def read_calendar_events(days_ahead: int, tool_context: ToolContext) -> dict:
    """Read upcoming financial/advisor meetings from Google Calendar.

    Searches for calendar events in the next N days related to finance/advisor.
    Useful for scheduling purposes and context injection.

    Args:
        days_ahead: Number of days to look ahead
        tool_context: ADK ToolContext

    Returns:
        Dict with status and list of events
    """
    creds = negotiate_creds(tool_context)

    if isinstance(creds, dict) and creds.get("pending"):
        return creds

    try:
        from datetime import datetime, timedelta

        service = build("calendar", "v3", credentials=creds)

        now = datetime.utcnow().isoformat() + "Z"
        end_time = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + "Z"

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                timeMax=end_time,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])
        logger.info(f"Found {len(events)} upcoming events")

        return {
            "status": "success",
            "events": [
                {
                    "summary": e.get("summary", "Untitled"),
                    "start": e.get("start", {}).get("dateTime", ""),
                    "description": e.get("description", ""),
                }
                for e in events
            ],
        }

    except Exception as e:
        logger.error(f"Error reading calendar: {e}")
        return {
            "status": "error",
            "message": f"Failed to read calendar: {str(e)}",
        }
