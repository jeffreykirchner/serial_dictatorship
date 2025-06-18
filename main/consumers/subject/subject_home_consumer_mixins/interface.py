
import json
import logging
import re

from asgiref.sync import sync_to_async
from main.decorators import check_message_for_me
from main.globals import chat_gpt_generate_completion
from django.utils.html import strip_tags

from main.models import SessionPlayer
from main.models import SessionEvent

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
    async def update_choices_simultaneous(self, event):
        '''
        update the choices made by the subject
        '''

        event_data = json.loads(event["group_data"])

        await self.send_message(message_to_self=event_data, message_to_subjects=None, message_to_staff=None, 
                                message_type=event['type'], send_to_client=True, send_to_group=False)
        
    @check_message_for_me
    async def update_choices_sequential(self, event):
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

        session_player = await SessionPlayer.objects.select_related('parameter_set_player__parameter_set_group').aget(id=self.session_player_id)

        prompt = strip_tags(event_data["prompt"]).strip()

        session_player.chat_gpt_prompt.append({
            "role": "user",
            "content":prompt,
        })

        response = await sync_to_async(chat_gpt_generate_completion, thread_sensitive=self.thread_sensitive)(session_player.chat_gpt_prompt)
        response = json.loads(response)
        # logger.info(f"ChatGPT response: {response}")
        
        content = ""
        try:
            content = response['choices'][0]['message']['content']
            code_found = 0

            if "<button" in content.lower():
                code_found = 1
            
            if "script" in content.lower():
                code_found = 1
            
            # # if "fetch" in content.lower():
            # #     content = "Error: Invalid prompt"
            
            # if "form" in content.lower():
            #     content = "Error: Invalid prompt"
            
            # if "xmlhttprequest " in content.lower():
            #     content = "Error: Invalid prompt"

            # if "img" in content.lower():
            #     content = "Error: Invalid prompt"
            
            if "a href" in content.lower():
                code_found = 1

            # #remove any html events but leave tags
            # content = re.sub(r'\s+on\w+\s*=\s*(".*?"|\'.*?\'|[^\s>]+)', '', content, flags=re.IGNORECASE)

            
            # if strip_tags(content) != content:
            #    code_found = True

            session_player.chat_gpt_prompt.append({
                "role": "assistant",
                "content": content,
                "code_found": code_found
            })

        except Exception as e:
            content = "Error: Invalid prompt"
            session_player.chat_gpt_prompt.pop()  # remove last user prompt
        
        # Save the updated chat_gpt_prompt to the session_player
        await session_player.asave()

        result = {
            "status": "success",            
            "response": {"role":"assistant", "content": content, "code_found": code_found},
        }

        result_staff = {"prompt": prompt,
                        "response": content,
                        "code_found": code_found,
                        "session_player_id": self.session_player_id}

        # store event
        await SessionEvent.objects.acreate(session_id=self.session_id, 
                            session_player_id=session_player.id,
                            type="chat_gpt_prompt",
                            period_number=event_data["current_period"],
                            group_number=session_player.parameter_set_player.parameter_set_group_id,
                            data=result_staff)
        
        # Send the response back to the client
        await self.send_message(message_to_self=result, message_to_subjects=None, message_to_staff=result_staff, 
                                message_type=event['type'], send_to_client=True, send_to_group=True)
    
    async def update_process_chat_gpt_prompt(self, event):
        '''
        ignore chat gpt prompt
        '''
        pass

    async def clear_chat_gpt_history(self, event):
        '''
        clear the chat gpt history
        '''
        session_player = await SessionPlayer.objects.aget(id=self.session_player_id)
        await sync_to_async(session_player.setup_chat_gpt_prompt, thread_sensitive=self.thread_sensitive)()
       
        result = {
            "status": "success",
            "chat_history" : await sync_to_async(session_player.get_chat_display_history)(),
        }

        result_staff = {"session_player_id": self.session_player_id}

        # Send the response back to the client
        await self.send_message(message_to_self=result, message_to_subjects=None, message_to_staff=result_staff, 
                                message_type=event['type'], send_to_client=True, send_to_group=True)
    
    async def update_clear_chat_gpt_history(self, event):
        '''
        ignore clear chat gpt history
        '''
        pass

        