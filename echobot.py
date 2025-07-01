from botbuilder.core import TurnContext, ActivityHandler
from botbuilder.schema import ActivityTypes, ChannelAccount
import logging

logger = logging.getLogger(__name__)

class EchoBot(ActivityHandler):
    async def on_members_added_activity(self, members_added : ChannelAccount, turn_context: TurnContext):
        logger.info("Conversation update detected.")
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(f"Hello {member.name}!")
                logger.info(f"Greeted {member.name}")
                
    async def on_message_activity(self, turn_context):
        logger.info(f"Received message: {turn_context.activity.text}")
        if turn_context.activity.text:
            await turn_context.send_activity("Echo: " + turn_context.activity.text)
        elif turn_context.activity.attachments:
            for attachment in turn_context.activity.attachments:
                if attachment.content_type == "audio/ogg":
                    await turn_context.send_activity("Sprachnachricht empfangen! (audio/ogg)")
                else:
                    await turn_context.send_activity(f"Attachment empfangen: {attachment.content_type}")
        else:
            await turn_context.send_activity("Nachricht ohne Text oder Anhang empfangen.")