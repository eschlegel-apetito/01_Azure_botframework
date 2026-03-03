from flask import Flask, request, Response
from botbuilder.schema import Activity
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botframework.connector.auth import (
    AuthenticationConfiguration, 
    MicrosoftAppCredentials,
    SimpleCredentialProvider
)
from azure.identity import ManagedIdentityCredential, DefaultAzureCredential
import asyncio
import os
import traceback

from echobot import EchoBot
import logging

app = Flask(__name__)
loop = asyncio.get_event_loop()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting Flask app...")

def mask_secret(value, show_chars=4):
    """Maskiert Secrets, zeigt nur die ersten X Zeichen"""
    if not value:
        return "<empty>"
    if len(value) <= show_chars:
        return "***"
    return value[:show_chars] + "***" + value[-show_chars:]

def log_env_vars():
    """Logge alle Microsoft-relevanten Umgebungsvariablen"""
    logger.info("=" * 80)
    logger.info("ENVIRONMENT VARIABLES:")
    logger.info("=" * 80)
    
    relevant_keys = [
        "MicrosoftAppId",
        "MicrosoftAppPassword", 
        "MicrosoftAppType",
        "MicrosoftAppTenantId",
        "ConnectionName",
        "MSI_ENDPOINT",
        "MSI_SECRET",
        "IDENTITY_ENDPOINT",
        "IDENTITY_HEADER"
    ]
    
    for key in relevant_keys:
        value = os.environ.get(key, "<not set>")
        if "Password" in key or "SECRET" in key or "HEADER" in key:
            display_value = mask_secret(value) if value != "<not set>" else value
        else:
            display_value = value
        logger.info(f"  {key}: {display_value}")
    
    logger.info("=" * 80)

log_env_vars()

try:
    logger.info("Initializing BotFrameworkAdapterSettings...")
    # Für Azure Deployment: App ID und App Password aus Umgebungsvariablen lesen
    app_id = os.environ.get("MicrosoftAppId", "")
    app_type = os.environ.get("MicrosoftAppType", "")
    tenant_id = os.environ.get("MicrosoftAppTenantId", "")
    
    logger.info(f"App Type: {app_type}")
    logger.info(f"App ID: {app_id}")
    logger.info(f"Tenant ID: {tenant_id}")
    
    # Bei Managed Identity kein Password verwenden
    if app_type in ["UserAssignedMSI", "ManagedIdentity"]:
        logger.info("Using Managed Identity authentication - setting empty password")
        app_password = ""
    else:
        app_password = os.environ.get("MicrosoftAppPassword", "")
        logger.info(f"Using password authentication - password present: {bool(app_password)}")
        logger.info(f"Password (masked): {mask_secret(app_password)}")
    
    # Credential Provider für Managed Identity
    logger.info("Creating credential_provider...")
    credential_provider = SimpleCredentialProvider(app_id, app_password)
    logger.info("credential_provider created successfully")
    
    logger.info("Creating BotFrameworkAdapterSettings...")
    botadapter_settings = BotFrameworkAdapterSettings(
        app_id=app_id, 
        app_password=app_password,
        credential_provider=credential_provider
    )
    logger.info("BotFrameworkAdapterSettings initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing BotFrameworkAdapterSettings: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise

logger.info("Creating BotFrameworkAdapter...")
botadapter = BotFrameworkAdapter(botadapter_settings)
logger.info("BotFrameworkAdapter created successfully")

ebot = EchoBot()


@app.route("/api/messages", methods=["POST"])
def messages():
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Raw body: {request.data}")
    if "application/json" in request.headers.get("content-type", ""):
        jsonmessage = request.json
        logger.info(f"Received JSON message: {jsonmessage}")
    else:
        logger.error("Unsupported content-type: %s", request.headers.get("content-type", ""))
        return Response("Unsupported Media Type", status=415)

    activity = Activity().deserialize(jsonmessage)

    async def turn_call(turn_context):
        try:
            logger.info("turn_call: Starting turn context processing")
            await ebot.on_turn(turn_context)
            logger.info("turn_call: Completed turn context processing")
        except Exception as e:
            logger.error(f"turn_call: Error in on_turn: {e}")
            logger.error(f"turn_call: Traceback: {traceback.format_exc()}")
            raise

    # Verarbeite die Aktivität
    try:
        auth_header = request.headers.get("Authorization", "")
        logger.info(f"Auth header present: {bool(auth_header)}")
        logger.info(f"Auth header length: {len(auth_header) if auth_header else 0}")
        logger.info(f"Activity type: {activity.type}")
        logger.info(f"Activity channel_id: {activity.channel_id}")
        logger.info(f"Activity service_url: {activity.service_url}")
        
        logger.info("Creating process_activity task...")
        task = loop.create_task(botadapter.process_activity(activity, auth_header, turn_call))
        logger.info("Running process_activity task...")
        loop.run_until_complete(task)
        logger.info("process_activity completed successfully")
    except Exception as e:
        logger.error(f"Error processing activity: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return Response("Error processing activity", status=500)

    # Gebe eine HTTP-200-Antwort zurück
    return Response(status=200)

if __name__ == "__main__":
    # Für lokale Entwicklung
    port = int(os.environ.get("PORT", 3978))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3978))
    app.run(host="0.0.0.0", port=port)