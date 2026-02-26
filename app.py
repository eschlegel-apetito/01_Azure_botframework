from flask import Flask, request, Response
from botbuilder.schema import Activity
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botframework.connector.auth import AuthenticationConfiguration, SimpleChannelProvider
import asyncio
import os

from echobot import EchoBot
import logging

app = Flask(__name__)
loop = asyncio.get_event_loop()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting Flask app...")

try:
    logger.info("Initializing BotFrameworkAdapterSettings...")
    # Für Azure Deployment: App ID und App Password aus Umgebungsvariablen lesen
    app_id = os.environ.get("MicrosoftAppId", "")
    app_password = os.environ.get("MicrosoftAppPassword", "")
    tenantId= os.environ.get("TenantId", "")
    
    # Channel Service für Sweden Central Region
    channel_service = "https://swedencentral.api.botframework.com"
    channel_provider = SimpleChannelProvider(channel_service=channel_service)
    
    AUTH_CONFIG = AuthenticationConfiguration(tenant_id=tenantId)
    botadapter_settings = BotFrameworkAdapterSettings(
        app_id=app_id, 
        app_password=app_password, 
        channel_provider=channel_provider,
        auth_configuration=AUTH_CONFIG
    )
    logger.info("BotFrameworkAdapterSettings initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing BotFrameworkAdapterSettings: {e}")
    raise

botadapter = BotFrameworkAdapter(botadapter_settings)

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
        await ebot.on_turn(turn_context)

    # Verarbeite die Aktivität
    try:
        auth_header = request.headers.get("Authorization", "")
        task = loop.create_task(botadapter.process_activity(activity, auth_header, turn_call))
        loop.run_until_complete(task)
    except Exception as e:
        logger.error(f"Error processing activity: {e}")
        return Response("Error processing activity", status=500)

    # Gebe eine HTTP-200-Antwort zurück
    return Response(status=200)

if __name__ == "__main__":
    # Für lokale Entwicklung
    port = int(os.environ.get("PORT", 3978))
    app.run(host="0.0.0.0", port=port)