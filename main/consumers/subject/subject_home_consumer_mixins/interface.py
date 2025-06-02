
import json
from main.decorators import check_message_for_me

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


        