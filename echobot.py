from botbuilder.core import TurnContext, ActivityHandler
from botbuilder.schema import ActivityTypes, ChannelAccount
import logging
import traceback

logger = logging.getLogger(__name__)

class EchoBot(ActivityHandler):
    async def on_members_added_activity(self, members_added : ChannelAccount, turn_context: TurnContext):
        try:
            logger.info("Conversation update detected.")
            for member in members_added:
                if member.id != turn_context.activity.recipient.id:
                    await turn_context.send_activity(f"Hello {member.name}!")
                    logger.info(f"Greeted {member.name}")
        except Exception as e:
            logger.error(f"Error in on_members_added_activity: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
                
    async def on_message_activity(self, turn_context):
        try:
            logger.info(f"on_message_activity: Starting")
            logger.info(f"Activity text: {turn_context.activity.text}")
            logger.info(f"Activity type: {turn_context.activity.type}")
            logger.info(f"Turn context type: {type(turn_context)}")
            
            if turn_context.activity.text:
                logger.info(f"Sending echo response...")
                await turn_context.send_activity("Echo: " + turn_context.activity.text)
                logger.info(f"Echo response sent successfully")
            elif turn_context.activity.attachments:
                for attachment in turn_context.activity.attachments:
                    if attachment.content_type == "audio/ogg":
                        await turn_context.send_activity("Sprachnachricht empfangen! (audio/ogg)")
                    else:
                        await turn_context.send_activity(f"Attachment empfangen: {attachment.content_type}")
            else:
                await turn_context.send_activity("Nachricht ohne Text oder Anhang empfangen.")
            
            logger.info(f"on_message_activity: Completed successfully")
        except Exception as e:
            logger.error(f"Error in on_message_activity: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise