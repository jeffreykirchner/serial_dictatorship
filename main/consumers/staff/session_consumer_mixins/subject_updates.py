
import logging
import math
import json

from decimal import Decimal

from datetime import datetime, timedelta

from django.utils.html import strip_tags

from main.models import SessionPlayer
from main.models import Session
from main.models import SessionEvent

from main.globals import ExperimentPhase
from main.globals import SubjectStatus

import main

class SubjectUpdatesMixin():
    '''
    subject updates mixin for staff session consumer
    '''

    async def update_connection_status(self, event):
        '''
        handle connection status update from group member
        '''
        logger = logging.getLogger(__name__) 
        event_data = event["data"]

        #update not from a client
        if event_data["value"] == "fail":
            if not self.session_id:
                self.session_id = event["session_id"]

            # logger.info(f"update_connection_status: event data {event}, channel name {self.channel_name}, group name {self.room_group_name}")

            if "session" in self.room_group_name:
                #connection from staff screen
                if event["connect_or_disconnect"] == "connect":
                    # session = await Session.objects.aget(id=self.session_id)
                    self.controlling_channel = event["sender_channel_name"]

                    if self.channel_name == self.controlling_channel:
                        # logger.info(f"update_connection_status: controller {self.channel_name}, session id {self.session_id}")
                        await Session.objects.filter(id=self.session_id).aupdate(controlling_channel=self.controlling_channel) 
                        await self.send_message(message_to_self=None, message_to_group={"controlling_channel" : self.controlling_channel},
                                                message_type="set_controlling_channel", send_to_client=False, send_to_group=True)
                else:
                    #disconnect from staff screen
                    pass                   
            return
        
        subject_id = event_data["result"]["id"]

        session_player = await SessionPlayer.objects.aget(id=subject_id)
        event_data["result"]["name"] = session_player.name
        event_data["result"]["student_id"] = session_player.student_id
        event_data["result"]["current_instruction"] = session_player.current_instruction
        event_data["result"]["survey_complete"] = session_player.survey_complete
        event_data["result"]["instructions_finished"] = session_player.instructions_finished

        await self.send_message(message_to_self=event_data, message_to_group=None,
                                message_type=event['type'], send_to_client=True, send_to_group=False)

    async def update_set_controlling_channel(self, event):
        '''
        only for subject screens
        '''
        pass

    async def update_name(self, event):
        '''
        send update name notice to staff screens
        '''

        event_data = event["staff_data"]

        await self.send_message(message_to_self=event_data, message_to_group=None,
                                message_type=event['type'], send_to_client=True, send_to_group=False)

    async def update_next_instruction(self, event):
        '''
        send instruction status to staff
        '''

        event_data = event["staff_data"]

        await self.send_message(message_to_self=event_data, message_to_group=None,
                                message_type=event['type'], send_to_client=True, send_to_group=False)
    
    async def update_finish_instructions(self, event):
        '''
        send instruction status to staff
        '''

        event_data = event["staff_data"]

        await self.send_message(message_to_self=event_data, message_to_group=None,
                                message_type=event['type'], send_to_client=True, send_to_group=False)
    
    async def update_survey_complete(self, event):
        '''
        send survey complete update
        '''
        event_data = event["data"]

        await self.send_message(message_to_self=event_data, message_to_group=None,
                                message_type=event['type'], send_to_client=True, send_to_group=False)
    
    async def choices(self, event):
        '''
        take choices from subject
        '''
        if self.controlling_channel != self.channel_name:
            return
        
        logger = logging.getLogger(__name__)
        
        event_data = event["message_text"]
        status = "success"
        error_message = ""

        try:
            choices = event_data["choices"]    
        except KeyError:
            logger.warning(f"choices: invalid choices, {event['message_text']}")
            return
        
        player_id = self.session_players_local[event["player_key"]]["id"]
        session_player = self.world_state_local["session_players"][str(player_id)]
        groups = self.world_state_local["groups"]

        #check if there is one choice per rank
        if len(choices) != self.parameter_set_local["group_size"]:
            status = "fail"
            error_message = "Rank all choices."

        #choices must be an array of integers
        elif not all(isinstance(c, int) for c in choices):
            status = "fail"
            error_message = "Choices must be whole numbers."

        #the minium value for a choice is 1 and the maximum is group_size
        elif any(c < 1 or c > self.parameter_set_local["group_size"] for c in choices):
            status = "fail"
            error_message = "Choices must be between 1 and " + str(self.parameter_set_local["group_size"]) + "."

        #check if there are duplicate choices
        elif len(choices) != len(set(choices)):
            status = "fail"
            error_message = "Choices must be unique."

        if status == "success":    
            self.world_state_local["choices"][str(player_id)] = choices
            session_player["status"] = SubjectStatus.FINISHED_RANKING

            self.session_events.append(SessionEvent(session_id=self.session_id, 
                                        session_player_id=player_id,
                                        type=event['type'],
                                        period_number=self.world_state_local["current_period"],
                                        time_remaining=self.world_state_local["time_remaining"],
                                        data=event_data,))
            
            await SessionEvent.objects.abulk_create(self.session_events, ignore_conflicts=True)
            self.session_events = []

            #check if all players have made choices
            if len(self.world_state_local["choices"]) == len(self.world_state_local["session_players"]):
                #all players have made choices, send to server
                outcome = {}
                
                current_period = self.world_state_local["current_period"]

                for i in self.world_state_local["session_players"]:
                    player = self.world_state_local["session_players"][i]
                    player["status"] = SubjectStatus.REVIEWING_RESULTS

                period_results = {}
                for g in groups:
                    outcome[g] = {"payments": {}}
                    group = groups[g]
                    for p in group["session_players_order"]:
                        # player_id = self.world_state_local["session_players"][str(p)]
                        player_choices = self.world_state_local["choices"][str(p)]

                        #loop through group[values][current_period] and find the next available value according to rank
                        outer_break = False
                        for i in range(len(player_choices)):
                            for c in player_choices:
                                if c == i+1 and not group["values"][str(current_period)][i]["owner"]:
                                    group["values"][str(current_period)][i]["owner"] = p
                                    period_results[str(p)] = {}
                                    period_results[str(p)]["prize"] = group["values"][str(current_period)][i]["value"]
                                    self.world_state_local["session_players"][str(p)]["earnings"] = Decimal(group["values"][str(current_period)][i]["value"]) + \
                                                                                                    Decimal(self.world_state_local["session_players"][str(p)]["earnings"])    
                                    outer_break = True
                                    break
                            
                            if outer_break:
                                break
                        
                        #store period results
                        period_results[str(p)]["priority_score"] = group["session_players"][str(p)][str(current_period)]["priority_score"]
                        period_results[str(p)]["order"] = group["session_players"][str(p)][str(current_period)]["order"]
                        period_results[str(p)]["period_number"] = current_period
                        
                        period_results[str(p)]["values"] = []
                        for i in range(len(player_choices)):
                            period_results[str(p)]["values"].append({
                                "value": group["values"][str(current_period)][i]["value"],
                                "rank": player_choices[i],
                            })

                        session_player = await SessionPlayer.objects.aget(id=p)
                        session_player.period_results.append(period_results[str(p)])
                        await session_player.asave()

                result = {"period_results": period_results,
                          "session_players": self.world_state_local["session_players"],}

                await self.send_message(message_to_self=None, message_to_group=result,
                                        message_type="result", send_to_client=False, send_to_group=True)
            else:
                 # there was an error with the choices
                result = {"status": status, 
                          "error_message": error_message,
                          "player_status":session_player["status"]}
                await self.send_message(message_to_self=None, message_to_group=result,
                                        message_type=event['type'], send_to_client=False, 
                                        send_to_group=True, target_list=[player_id])
            
            await self.store_world_state(force_store=True)
        else:
            # there was an error with the choices
            result = {"status": status, "error_message": error_message}
            await self.send_message(message_to_self=None, message_to_group=result,
                                    message_type=event['type'], send_to_client=False, 
                                    send_to_group=True, target_list=[player_id])
            

    async def update_choices(self, event):
        '''
        update choices from subject
        '''
        pass

    async def update_result(self, event):
        '''
        send the result of the period choices to the subject screens
        '''
        event_data = json.loads(event["group_data"])

        await self.send_message(message_to_self=event_data, message_to_group=None,
                                message_type=event['type'], send_to_client=True, send_to_group=False)
    
    async def ready_to_go_on(self, event):
        '''
        subject has finished reviewing results and is ready to go on
        '''
        if self.controlling_channel != self.channel_name:
            return
        
        logger = logging.getLogger(__name__)

        event_data = event["message_text"]

        player_id = self.session_players_local[event["player_key"]]["id"]
        session_player = self.world_state_local["session_players"][str(player_id)]

        session_player["status"] = SubjectStatus.WAITING

        # store event
        self.session_events.append(SessionEvent(session_id=self.session_id, 
                                    session_player_id=player_id,
                                    type=event['type'],
                                    period_number=self.world_state_local["current_period"],
                                    time_remaining=self.world_state_local["time_remaining"],
                                    data=event_data,))
        
        await SessionEvent.objects.abulk_create(self.session_events, ignore_conflicts=True)
        self.session_events = []

        # check if all subjects are ready
        all_ready = True
        for i in self.world_state_local["session_players"]:
            if self.world_state_local["session_players"][i]["status"] != SubjectStatus.WAITING:
                all_ready = False
                break

        if all_ready:
            # all subjects are ready, go to next period
            self.world_state_local["current_period"] += 1
            self.world_state_local["time_remaining"] = self.parameter_set_local["period_length"]

            # reset choices and set session players status to 'Ranking'
            for i in self.world_state_local["session_players"]:
                self.world_state_local["session_players"][i]["status"] = SubjectStatus.RANKING
  
            self.world_state_local["choices"] = {}
            
            result = {
                "current_period": self.world_state_local["current_period"],                
            }

            # send message to subject screens to go to next period
            await self.send_message(message_to_self=None, message_to_group=result,
                                    message_type="start_next_period", send_to_client=False, send_to_group=True)

        await self.store_world_state(force_store=True)
    
    async def update_start_next_period(self, event):
        '''
        send start next period to subject screens
        '''
        event_data = event["group_data"]

        await self.send_message(message_to_self=event_data, message_to_group=None,
                                message_type=event['type'], send_to_client=True, send_to_group=False)


   
                                      
    

                                
        

