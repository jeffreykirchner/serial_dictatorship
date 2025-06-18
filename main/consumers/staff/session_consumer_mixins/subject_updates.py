
import logging
import math
import json

from decimal import Decimal

from datetime import datetime, timedelta

from django.utils.html import strip_tags

from main.models import SessionPlayer
from main.models import Session
from main.models import SessionEvent
from main.models import SessionPeriod

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

    async def choices_simultaneous(self, event):
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
        parameter_set_player = self.parameter_set_local["parameter_set_players"][str(session_player["parameter_set_player_id"])]
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
                                        group_number=parameter_set_player["parameter_set_group"],
                                        data=event_data))

            await SessionEvent.objects.abulk_create(self.session_events, ignore_conflicts=True)
            self.session_events = []

            #check if all players have made choices
            if len(self.world_state_local["choices"]) == len(self.world_state_local["session_players"]):
                #all players have made choices, send to server                
                current_period = self.world_state_local["current_period"]

                for i in self.world_state_local["session_players"]:
                    player = self.world_state_local["session_players"][i]
                    player["status"] = SubjectStatus.REVIEWING_RESULTS

                period_results = {}
                for g in groups:
      
                    group = groups[g]
                    for p in group["player_order"][str(current_period)]:
                        # player_id = self.world_state_local["session_players"][str(p)]
                        player_choices = self.world_state_local["choices"][str(p)]

                        #loop through group[values][current_period] and find the next available value according to rank
                        outer_break = False
                        for i in range(len(player_choices)):
                            for j in range(len(player_choices)):

                                if player_choices[j] == i+1 and not group["values"][str(current_period)][j]["owner"]:
                                    group["values"][str(current_period)][j]["owner"] = p
                                    period_results[str(p)] = {}
                                    period_results[str(p)]["prize"] = group["values"][str(current_period)][j]["value"]
                                    self.world_state_local["session_players"][str(p)]["earnings"] = Decimal(group["values"][str(current_period)][j]["value"]) + \
                                                                                                    Decimal(self.world_state_local["session_players"][str(p)]["earnings"])    
                                    outer_break = True
                                    break
                            
                            if outer_break:
                                break
                        
                        period_results[str(p)]["expected_order"] = True
                        #check if player value of choices are in order from highest to lowest
                        for i in range(len(player_choices)-1):
                            v1 = player_choices[i]-1
                            v2 = player_choices[i+1]-1
                            if group["values"][str(current_period)][v1]["value"] < group["values"][str(current_period)][v2]["value"]:
                                period_results[str(p)]["expected_order"] = False
                                break

                        #store period results
                        period_results[str(p)]["priority_score"] = group["session_players"][str(p)][str(current_period)]["priority_score"]
                        period_results[str(p)]["order"] = group["session_players"][str(p)][str(current_period)]["order"]
                        period_results[str(p)]["period_number"] = current_period
                        
                        period_results[str(p)]["values"] = []
                        for i in range(len(player_choices)):
                            period_results[str(p)]["values"].append({
                                "value": group["values"][str(current_period)][i]["value"],
                                "owner": group["values"][str(current_period)][i]["owner"],
                                "rank": player_choices[i],
                            })

                        session_player = await SessionPlayer.objects.aget(id=p)
                        session_player.period_results.append(period_results[str(p)])
                        await session_player.asave()

                await SessionPeriod.objects.filter(session_id=self.session_id,period_number=current_period) \
                                           .aupdate(summary_data=period_results)

                result = {"period_results": period_results,
                          "session_players": self.world_state_local["session_players"],}

                await self.send_message(message_to_self=None, message_to_group=result,
                                        message_type="result", send_to_client=False, send_to_group=True)
            else:
               #send status player and staff screens
                result = {"status": status, 
                          "error_message": error_message,
                          "player_id": player_id,
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
            

    async def update_choices_simultaneous(self, event):
        '''
        update choices from subject
        '''
        event_data = json.loads(event["group_data"])

        await self.send_message(message_to_self=event_data, message_to_group=None,
                                message_type=event['type'], send_to_client=True, send_to_group=False)

    async def choices_sequential(self, event):
        '''
        take choice from subject
        '''
        if self.controlling_channel != self.channel_name:
            return
        
        logger = logging.getLogger(__name__)
        
        event_data = event["message_text"]
        status = "success"
        error_message = ""

        try:
            choice = event_data["choice"]
        except KeyError:
            logger.warning(f"choice: invalid choice, {event['message_text']}")
            return
        
        player_id = self.session_players_local[event["player_key"]]["id"]
        session_player = self.world_state_local["session_players"][str(player_id)]
        parameter_set_player = self.parameter_set_local["parameter_set_players"][str(session_player["parameter_set_player_id"])]
        groups = self.world_state_local["groups"]
        group = groups[str(parameter_set_player["parameter_set_group"])]
        current_period = self.world_state_local["current_period"]

        #check if choice is an integer
        if not isinstance(choice, int):
            status = "fail"
            error_message = "Select a prize."
        #the minium value for a choice is 0 and the maximum is group_size-1
        elif choice < 0 or choice >= self.parameter_set_local["group_size"]:
            status = "fail"
            error_message = f"Choice must be between 0 and {self.parameter_set_local['group_size'] - 1}."
        #check if is this player's turn
        elif group["player_order"][str(current_period)][group["active_player_group_index"]] != str(player_id):
            status = "fail"
            error_message = "It is not your turn to choose."
        #check if player has already made a choice
        elif str(player_id) in self.world_state_local["choices"]:
            status = "fail"
            error_message = "You have already made a choice."

        if status == "success":
            self.world_state_local["choices"][str(player_id)] = choice
            session_player["status"] = SubjectStatus.FINISHED_RANKING
            group["values"][str(current_period)][choice]["owner"] = player_id
            group["values"][str(current_period)][choice]["expected_order"] = True

            #check if there is a remaining higher unclaimed value
            for i in group["values"][str(current_period)]:
                if not i["owner"] and i["value"] > group["values"][str(current_period)][choice]["value"]:
                    group["values"][str(current_period)][choice]["expected_order"] = False
            
            self.session_events.append(SessionEvent(session_id=self.session_id, 
                                        session_player_id=player_id,
                                        type=event['type'],
                                        period_number=self.world_state_local["current_period"],
                                        group_number=parameter_set_player["parameter_set_group"],
                                        data=event_data,))
            
            await SessionEvent.objects.abulk_create(self.session_events, ignore_conflicts=True)
            self.session_events = []

            #check if all players have made choices
            if len(self.world_state_local["choices"]) == len(self.world_state_local["session_players"]):
                #all players have made choices, send to server

                for i in self.world_state_local["session_players"]:
                    player = self.world_state_local["session_players"][i]
                    player["status"] = SubjectStatus.REVIEWING_RESULTS

                period_results = {}

                for g in groups: 
                    group = groups[g]
                    for p in group["player_order"][str(current_period)]:
                        # player_id = self.world_state_local["session_players"][str(p)]
                        player_choices = self.world_state_local["choices"][str(p)]

                        #loop through group[values][current_period] and find the next available value according to rank

                        period_results[str(p)] = {}
                        prize_index = self.world_state_local["choices"][str(p)]
                        period_results[str(p)]["prize"] = group["values"][str(current_period)][prize_index]["value"]
                        self.world_state_local["session_players"][str(p)]["earnings"] = Decimal(group["values"][str(current_period)][prize_index]["value"]) + \
                                                                                        Decimal(self.world_state_local["session_players"][str(p)]["earnings"])    

                        #store period results
                        period_results[str(p)]["priority_score"] = group["session_players"][str(p)][str(current_period)]["priority_score"]
                        period_results[str(p)]["order"] = group["session_players"][str(p)][str(current_period)]["order"]
                        period_results[str(p)]["period_number"] = current_period
                        period_results[str(p)]["expected_order"] = group["values"][str(current_period)][prize_index]["expected_order"]
                        
                        period_results[str(p)]["values"] = []
                        for i in range(len(group["values"][str(current_period)])):
                            period_results[str(p)]["values"].append({
                                "value": group["values"][str(current_period)][i]["value"],
                                "owner": group["values"][str(current_period)][i]["owner"],
                                "rank": 1 if i == prize_index else 0,
                            })

                        session_player = await SessionPlayer.objects.aget(id=p)
                        session_player.period_results.append(period_results[str(p)])
                        await session_player.asave()

                await SessionPeriod.objects.filter(session_id=self.session_id,period_number=current_period) \
                                           .aupdate(summary_data=period_results)

                result = {"period_results": period_results,
                          "values": group["values"][str(current_period)],
                          "session_players": self.world_state_local["session_players"],}

                await self.send_message(message_to_self=None, message_to_group=result,
                                        message_type="result", send_to_client=False, send_to_group=True)
                
            else:
                #send choice to the group
                group["active_player_group_index"] += 1

                result = {"status": status,
                          "error_message": error_message,
                          "active_player_group_index": group["active_player_group_index"],
                          "values": group["values"][str(current_period)],
                          "player_id": player_id,
                          "player_status": session_player["status"],
                          }
                await self.send_message(message_to_self=None, message_to_group=result,
                                        message_type=event['type'], send_to_client=False, 
                                        send_to_group=True, target_list=group["session_players_order"])
            
            await self.store_world_state(force_store=True)
        else:
            # there was an error with the choices
            result = {"status": status, "error_message": error_message}
            await self.send_message(message_to_self=None, message_to_group=result,
                                    message_type=event['type'], send_to_client=False, 
                                    send_to_group=True, target_list=[player_id])


    async def update_choices_sequential(self, event):
        '''
        update choice from subject
        '''
        event_data = json.loads(event["group_data"])

        await self.send_message(message_to_self=event_data, message_to_group=None,
                                message_type=event['type'], send_to_client=True, send_to_group=False)
        
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
        parameter_set_player = self.parameter_set_local["parameter_set_players"][str(session_player["parameter_set_player_id"])]

        session_player["status"] = SubjectStatus.WAITING

        # store event
        self.session_events.append(SessionEvent(session_id=self.session_id, 
                                    session_player_id=player_id,
                                    type=event['type'],
                                    period_number=self.world_state_local["current_period"],
                                    group_number=parameter_set_player["parameter_set_group"],
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
            if self.world_state_local["current_period"] >= self.parameter_set_local["period_count"]:
                # all periods are complete
                self.world_state_local["current_experiment_phase"] = ExperimentPhase.NAMES

                result = {
                    "current_experiment_phase": self.world_state_local["current_experiment_phase"],
                    }
                # send message to subject screens to go to next period
                await self.send_message(message_to_self=None, message_to_group=result,
                                        message_type="show_name_input", send_to_client=False, send_to_group=True)
            else:
                # all subjects are ready, go to next period
                self.world_state_local["current_period"] += 1
                self.world_state_local["time_remaining"] = self.parameter_set_local["period_length"]

                # reset choices and set session players status to 'Ranking'
                for i in self.world_state_local["session_players"]:
                    self.world_state_local["session_players"][i]["status"] = SubjectStatus.RANKING
    
                # reset choices
                self.world_state_local["choices"] = {}

                #set active player group index to 0
                for g in self.world_state_local["groups"]:
                    group = self.world_state_local["groups"][g]
                    group["active_player_group_index"] = 0

                result = {
                    "current_period": self.world_state_local["current_period"],  
                    "active_player_group_index": 0,             
                }

                # send message to subject screens to go to next period
                await self.send_message(message_to_self=None, message_to_group=result,
                                        message_type="start_next_period", send_to_client=False, send_to_group=True)
        else:
            result = {
                "status": "success",
                "player_id": player_id,
                "player_status": session_player["status"],            
            }
            await self.send_message(message_to_self=result, message_to_group=None,
                                    message_type="update_status", send_to_client=True, send_to_group=False)
        
        await self.store_world_state(force_store=True)

        # send message to subject screens to go to next period

    async def update_start_next_period(self, event):
        '''
        send start next period to subject screens
        '''
        event_data = json.loads(event["group_data"])

        session_players = {i: {"status" : self.world_state_local["session_players"][i]["status"]} for i in self.world_state_local["session_players"]}

        event_data["session_players"] = session_players
        await self.send_message(message_to_self=event_data, message_to_group=None,
                                message_type=event['type'], send_to_client=True, send_to_group=False)
    
    async def update_show_name_input(self, event):
        '''
        send show name input to subject screens
        '''
        event_data = json.loads(event["group_data"])

        await self.send_message(message_to_self=event_data, message_to_group=None,
                                message_type=event['type'], send_to_client=True, send_to_group=False)
    
    async def update_process_chat_gpt_prompt(self, event):
        '''
        process chat gpt prompt from subject consumer
        '''
        event_data = event["staff_data"]

        await self.send_message(message_to_self=event_data, message_to_group=None,
                                message_type=event['type'], send_to_client=True, send_to_group=False)

    async def update_clear_chat_gpt_history(self, event):
        '''
        clear chat gpt history from subject consumer
        '''
        event_data = event["staff_data"]

        player_id = event_data["session_player_id"]     
        session_player = self.world_state_local["session_players"][str(player_id)]
        parameter_set_player = self.parameter_set_local["parameter_set_players"][str(session_player["parameter_set_player_id"])]

        # store event
        self.session_events.append(SessionEvent(session_id=self.session_id, 
                                    session_player_id=player_id,
                                    type="clear_chat_gpt_history",
                                    period_number=self.world_state_local["current_period"],
                                    group_number=parameter_set_player["parameter_set_group"],
                                    data=event_data,))
        
        await SessionEvent.objects.abulk_create(self.session_events, ignore_conflicts=True)
        self.session_events = []
        


   
                                      
    

                                
        

