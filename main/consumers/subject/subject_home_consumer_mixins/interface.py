
import json
import logging

from asgiref.sync import sync_to_async
from main.decorators import check_message_for_me
from main.globals import chat_gpt_generate_completion

from main.models import SessionPlayer

class InterfaceMixin():
    '''
    interface actions from subject screen mixin
    '''
    async def update_rescue_subject(self, event):
        '''
        update rescue subject
        '''

        event_data = json.loads(event["group_data"])

        await self.send_message(message_to_self=event_data, message_to_subjects=None, message_to_staff=None, 
                                message_type=event['type'], send_to_client=True, send_to_group=False)

    @check_message_for_me  
    async def update_choices(self, event):
        '''
        update the choices made by the subject
        '''

        event_data = json.loads(event["group_data"])

        await self.send_message(message_to_self=event_data, message_to_subjects=None, message_to_staff=None, 
                                message_type=event['type'], send_to_client=True, send_to_group=False)
        
    async def update_result(self, event):
        '''
        show the result of the period choices on the subject screen
        '''

        event_data = json.loads(event["group_data"])

        period_results = event_data["period_results"][str(self.session_player_id)]
        earnings = event_data["session_players"][str(self.session_player_id)]["earnings"]

        event_data = {"period_results": period_results, 
                      "earnings": earnings}

        await self.send_message(message_to_self=event_data, message_to_subjects=None, message_to_staff=None, 
                                message_type=event['type'], send_to_client=True, send_to_group=False)

    async def update_start_next_period(self, event):
        '''
        start the next period
        '''
        event_data = json.loads(event["group_data"])
        await self.send_message(message_to_self=event_data, message_to_subjects=None, message_to_staff=None, 
                                message_type=event['type'], send_to_client=True, send_to_group=False)
        
    async def update_show_name_input(self, event):
        '''
        show the name input field
        '''
        event_data = json.loads(event["group_data"])
        await self.send_message(message_to_self=event_data, message_to_subjects=None, message_to_staff=None, 
                                message_type=event['type'], send_to_client=True, send_to_group=False)

    async def process_chat_gpt_prompt(self, event):
        '''
        process the chat gpt prompt
        '''
        logger = logging.getLogger(__name__) 

        event_data = event["message_text"]
        status = "success"
        error_message = ""

        session_player = await SessionPlayer.objects.aget(id=self.session_player_id)

        session_player.chat_gpt_prompt.append({
            "role": "user",
            "content":event_data["prompt"],
        })

        response = await sync_to_async(chat_gpt_generate_completion, thread_sensitive=self.thread_sensitive)(session_player.chat_gpt_prompt)
        response = json.loads(response)
        logger.info(f"ChatGPT response: {response}")
        
        session_player.chat_gpt_prompt.append({
            "role": "assistant",
            "content": response['choices'][0]['message']['content']
        })

        # Save the updated chat_gpt_prompt to the session_player
        await session_player.asave()

        result = {
            "status": "success",            
            "response": {"role":"assistant", "content": response['choices'][0]['message']['content']},
        }

        # Send the response back to the client
        await self.send_message(message_to_self=result, message_to_subjects=None, message_to_staff=None, 
                                message_type=event['type'], send_to_client=True, send_to_group=False)

        