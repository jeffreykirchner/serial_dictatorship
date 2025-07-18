'''
session model
'''

from datetime import datetime
from tinymce.models import HTMLField
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from decimal import Decimal

import logging
import uuid
import csv
import io
import json
import random
import re
import string

from django.conf import settings

from django.dispatch import receiver
from django.db import models
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import strip_tags

import main

from main.models import ParameterSet

from main.globals import ExperimentPhase
from main.globals import SubjectStatus
from main.globals import round_up
from main.globals import ChatGPTMode

#experiment sessoin
class Session(models.Model):
    '''
    session model
    '''
    parameter_set = models.OneToOneField(ParameterSet, on_delete=models.CASCADE)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions_a")
    collaborators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="sessions_b")

    title = models.CharField(max_length=300, default="*** New Session ***")    #title of session
    start_date = models.DateField(default=now)                                 #date of session start

    channel_key = models.UUIDField(default=uuid.uuid4, editable=False, verbose_name = 'Channel Key')     #unique channel to communicate on
    session_key = models.UUIDField(default=uuid.uuid4, editable=False, verbose_name = 'Session Key')     #unique key for session to auto login subjects by id

    id_string = models.CharField(max_length=6, unique=True, null=True, blank=True)                       #unique string for session to auto login subjects by id

    controlling_channel = models.CharField(max_length = 300, default="")         #channel controlling session

    started =  models.BooleanField(default=False)                                #starts session and filll in session
   
    shared = models.BooleanField(default=False)                                  #shared session parameter sets can be imported by other users
    locked = models.BooleanField(default=False)                                  #locked models cannot be deleted

    invitation_text = HTMLField(default="", verbose_name="Invitation Text")       #inviataion email subject and text
    invitation_subject = HTMLField(default="", verbose_name="Invitation Subject")

    world_state = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True, verbose_name="Current Session State")       #world state at this point in session

    replay_data = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True, verbose_name="Replay Data")   

    website_instance_id = models.CharField(max_length=300, default="", verbose_name="Website Instance ID", null=True, blank=True)           #website instance from azure

    soft_delete =  models.BooleanField(default=False)                             #hide session if true

    timestamp = models.DateTimeField(auto_now_add=True)
    updated= models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def creator_string(self):
        return self.creator.email
    creator_string.short_description = 'Creator'

    class Meta:
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'
        ordering = ['-start_date']
        

    def get_start_date_string(self):
        '''
        get a formatted string of start date
        '''
        return  self.start_date.strftime("%#m/%#d/%Y")

    def get_group_channel_name(self):
        '''
        return channel name for group
        '''
        page_key = f"session-{self.id}"
        room_name = f"{self.channel_key}"
        return  f'{page_key}-{room_name}'
    
    def send_message_to_group(self, message_type, message_data):
        '''
        send socket message to group
        '''
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(self.get_group_channel_name(),
                                                {"type" : message_type,
                                                 "data" : message_data})

    def start_experiment(self):
        '''
        setup and start experiment
        '''

        self.started = True
        self.start_date = datetime.now()
        
        session_periods = []

        for i in range(self.parameter_set.period_count):
            session_periods.append(main.models.SessionPeriod(session=self, period_number=i+1))
        
        main.models.SessionPeriod.objects.bulk_create(session_periods)

        self.save()

        for i in self.session_players.all():
            i.start()

        self.setup_world_state()
        self.setup_summary_data()

    def setup_summary_data(self):
        '''
        setup summary data
        '''
        self.session_periods.all().update(summary_data=None)

    def setup_world_state(self):
        '''
        setup world state
        '''
        parameter_set  = self.parameter_set.json_for_session
        
        self.world_state = {"last_update":str(datetime.now()), 
                            "last_store":str(datetime.now()),
                            "session_players":{},
                            "session_players_order":[],
                            "current_period":1,
                            "current_experiment_phase":ExperimentPhase.INSTRUCTIONS if self.parameter_set.show_instructions else ExperimentPhase.RUN,
                            "time_remaining":self.parameter_set.period_length,
                            "timer_running":False,
                            "timer_history":[],
                            "started":True,
                            "finished":False,
                            "session_periods":{str(i.id) : i.json() for i in self.session_periods.all()},
                            "session_periods_order" : list(self.session_periods.all().values_list('id', flat=True)),
                            }
        
        inventory = {str(i):0 for i in list(self.session_periods.all().values_list('id', flat=True))}
        groups = {i:{"session_players":{}, "session_players_order":[], "values":{}, "priority_scores":{}, "player_order":{},"index_map":{},"active_player_group_index":0} for i in parameter_set["parameter_set_groups"]}

        #session periods
        # for i in self.world_state["session_periods"]:
        #     self.world_state["session_periods"][i]["consumption_completed"] = False
        
        #session players
        for i in self.session_players.prefetch_related('parameter_set_player').all().values('id',
                                                                                            'parameter_set_player__id'):
            v = {}
            v['earnings'] = 0
            v['status'] = SubjectStatus.RANKING if self.parameter_set.chat_gpt_mode == ChatGPTMode.OFF else SubjectStatus.CHATTING
            # v['history'] = {}
            v['parameter_set_player_id'] = i['parameter_set_player__id']
            self.world_state["session_players"][str(i['id'])] = v
            self.world_state["session_players_order"].append(i['id'])

            parameter_set_player = parameter_set["parameter_set_players"][str(i['parameter_set_player__id'])]
            parameter_set_group_id = parameter_set_player['parameter_set_group']

            groups[str(parameter_set_group_id)]['session_players'][str(i['id'])] = {}
            groups[str(parameter_set_group_id)]['session_players_order'].append(i['id'])

            groups[str(parameter_set_group_id)]["index_map"][str(parameter_set_player["group_index"])] = str(i['id'])

        #period groups
        for i in parameter_set["parameter_set_group_periods"]:
            parameter_set_group_period = parameter_set["parameter_set_group_periods"][i]
            group = groups[str(parameter_set_group_period["parameter_set_group"])]
            period_number = parameter_set_group_period["period_number"]

            #values
            group["values"][str(period_number)] = parameter_set_group_period["values"].split(",")

            #trim values
            group["values"][str(period_number)] = [{"value":v.strip(),"owner":None } for v in group["values"][str(period_number)]]
            
            #priority scores
            group["priority_scores"][str(period_number)] = parameter_set_group_period["priority_scores"].split(",")

            #player order
            group["player_order"][str(period_number)] = parameter_set_group_period["player_order"].split(",")
            
            #map player order to session player id
            for j in range(len(group["player_order"][str(period_number)])):
                group["player_order"][str(period_number)][j] = group["index_map"][str(group["player_order"][str(period_number)][j])]
  
            for j in range(len(group["player_order"][str(period_number)])): 
                session_player_id = group["player_order"][str(period_number)][j]   
                parameter_set_player_id = self.world_state["session_players"][str(session_player_id)]["parameter_set_player_id"]
                parameter_set_player = parameter_set["parameter_set_players"][str(parameter_set_player_id)]
                
                priority_score = group["priority_scores"][str(period_number)][parameter_set_player["group_index"]-1] 
                player_order = j+1          
                group["session_players"][str(session_player_id)][str(period_number)] = {"priority_score":priority_score,
                                                                                        "order":player_order,}


        self.world_state["groups"] = groups

        # current player choices and results
        self.world_state["choices"] = {}
        self.world_state["auto_submit"] = {}

        self.save()

    def reset_experiment(self):
        '''
        reset the experiment
        '''
        self.started = False

        #self.time_remaining = self.parameter_set.period_length
        #self.timer_running = False
        self.world_state ={}
        self.save()

        for p in self.session_players.all():
            p.reset()

        self.session_periods.all().delete()
        self.session_events.all().delete()

        # self.parameter_set.setup()
    
    def reset_connection_counts(self):
        '''
        reset connection counts
        '''
        self.session_players.all().update(connecting=False, connected_count=0)
    
    def get_current_session_period(self):
        '''
        return the current session period
        '''
        if not self.started:
            return None

        return self.session_periods.get(period_number=self.world_state["current_period"])

    async def aget_current_session_period(self):
        '''
        return the current session period
        '''
        if not self.started:
            return None

        return await self.session_periods.aget(period_number=self.world_state["current_period"])
    
    def update_player_count(self):
        '''
        update the number of session players based on the number defined in the parameterset
        '''

        self.session_players.all().delete()
    
        for count, i in enumerate(self.parameter_set.parameter_set_players.all()):
            new_session_player = main.models.SessionPlayer()

            new_session_player.session = self
            new_session_player.parameter_set_player = i
            new_session_player.player_number = i.player_number

            new_session_player.save()

    def user_is_owner(self, user):
        '''
        return turn is user is owner or an admin
        '''

        if user.is_staff:
            return True

        if user==self.creator:
            return True
        
        return False

    def get_chat_display_history(self):
        '''
        return chat gpt history for display
        '''

        chat_history = []

        #return last 10 session events
        for i in self.session_events.filter(type="chat_gpt_prompt").order_by('-timestamp').all()[:10]:

            #add i to front of list 
            chat_history.append(i.data)


        return chat_history

    def get_download_summary_csv(self):
        '''
        return data summary in csv format
        '''
        logger = logging.getLogger(__name__)
        
        world_state = self.world_state
        parameter_set_players = {}
        for i in self.session_players.all().values('id','player_number'):
            parameter_set_players[str(i['id'])] = i

        session_players = {}
        for i in self.session_players.all().values('id','player_number'):
            session_players[str(i['id'])] = i

        parameter_set = self.parameter_set.json()
        
        with io.StringIO() as output:

            writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
            
            top_row = ["Session ID", "Period", "Group", "Client #"]

            for i in range(parameter_set["group_size"]):
                top_row.append(f"Value {i+1}")

            top_row.append("Priority Score")
            top_row.append("Player Order")

            if parameter_set["experiment_mode"] == "Simultaneous":
                for i in range(parameter_set["group_size"]):
                    top_row.append(f"Choice {i+1}")

            top_row.append("Prize")
            top_row.append("Optimal Prize")
            top_row.append("Auto Submit")

            writer.writerow(top_row)

            for p in self.session_periods.all():
                summary_data = p.summary_data
                if not summary_data:
                    continue

                for i in summary_data:
                    session_player = world_state["session_players"][i]
                    parameter_set_player = parameter_set["parameter_set_players"][str(session_player["parameter_set_player_id"])]

                    row = []
                    row.append(self.id)
                    row.append(p.period_number)
                    row.append(parameter_set["parameter_set_groups"][str(parameter_set_player["parameter_set_group"])]["name"])
                    row.append(parameter_set_player["player_number"])

                    for j in summary_data[i]["values"]:
                        row.append(j["value"])
                    
                    row.append(summary_data[i]["priority_score"])
                    row.append(summary_data[i]["order"])

                    if parameter_set["experiment_mode"] == "Simultaneous":
                        for j in summary_data[i]["values"]:
                            row.append(j["rank"])
                    
                    row.append(summary_data[i]["prize"])
                    row.append(summary_data[i]["expected_order"])
                    row.append(summary_data[i]["auto_submit"])

                    writer.writerow(row)

            v = output.getvalue()
            output.close()

        return v
    
    def get_download_action_csv(self):
        '''
        return data actions in csv format
        '''
        with io.StringIO() as output:

            writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

            writer.writerow(["Session ID", "Period", "Group", "Client #", "Action","Info (Plain)", "Info (JSON)", "Timestamp"])

            world_state = self.world_state
            parameter_set_players = {}
            for i in self.session_players.all().values('id','player_number'):
                parameter_set_players[str(i['id'])] = i

            session_players = {}
            for i in self.session_players.all().values('id','player_number'):
                session_players[str(i['id'])] = i

            parameter_set = self.parameter_set.json()

            for p in self.session_events.exclude(type="world_state").all():
                writer.writerow([self.id,
                                p.period_number, 
                                parameter_set["parameter_set_groups"][str(p.group_number)]["name"], 
                                parameter_set_players[str(p.session_player_id)]["player_number"], 
                                p.type, 
                                self.action_data_parse(p.type, p.data, parameter_set, p.group_number, p.period_number, world_state),
                                p.data, 
                                p.timestamp])
            

            v = output.getvalue()
            output.close()

        return v

    def action_data_parse(self, type, data, parameter_set, group_number, period_number, world_state):
        '''
        return plain text version of action
        '''

        if type == "choices_sequential":
            v = f"choice: {world_state["groups"][str(group_number)]["values"][str(period_number)][data["choice"]-1]["value"]} | "
            v += f"Auto Submit: {data['auto_submit']}"
            return v
        elif type == "choices_simultaneous":
            s = "choices: "
            for c in data["choices"]:
                if s != "":
                    s += ", "
                s += world_state["groups"][str(group_number)]["values"][str(period_number)][c-1]["value"] 

            s += f" | Auto Submit: {data['auto_submit']}"
            return s
        elif type == "chat_gpt_prompt":
            return f'{data["prompt"]} | {strip_tags(data["response"])}'
        elif type == "ready_to_go_on":
            return f"Auto Submit: {data['auto_submit']}"
        elif type == "done_chatting":
            return f"Auto Submit: {data['auto_submit']}"
        
        return ""
    
    def get_download_recruiter_csv(self):
        '''
        return data recruiter in csv format
        '''
        with io.StringIO() as output:

            writer = csv.writer(output)

            parameter_set_players = {}
            for i in self.session_players.all().values('id','student_id'):
                parameter_set_players[str(i['id'])] = i

            for p in self.world_state["session_players"]:
                writer.writerow([parameter_set_players[p]["student_id"],
                                 round_up(Decimal(self.world_state["session_players"][p]["earnings"])/100,2)])

            v = output.getvalue()
            output.close()

        return v
    
    def get_download_payment_csv(self):
        '''
        return data payments in csv format
        '''
        with io.StringIO() as output:

            writer = csv.writer(output)

            writer.writerow(['Session', 'Date', 'Player', 'Name', 'Student ID', 'Earnings'])

            # session_players = self.session_players.all()

            # for p in session_players:
            #     writer.writerow([self.id, self.get_start_date_string(), p.player_number,p.name, p.student_id, p.earnings/100])

            parameter_set_players = {}
            for i in self.session_players.all().values('id', 'player_number', 'name', 'student_id'):
                parameter_set_players[str(i['id'])] = i

            for p in self.world_state["session_players"]:
                writer.writerow([self.id,
                                 self.get_start_date_string(),
                                 parameter_set_players[p]["player_number"],
                                 parameter_set_players[p]["name"],
                                 parameter_set_players[p]["student_id"],
                                 self.world_state["session_players"][p]["earnings"]])

            v = output.getvalue()
            output.close()

        return v
    
    def json(self):
        '''
        return json object of model
        '''
                                                                      
        return{
            "id":self.id,
            "title":self.title,
            "locked":self.locked,
            "start_date":self.get_start_date_string(),
            "started":self.started,
            "id_string":self.id_string,
            "parameter_set":self.parameter_set.json(),
            "session_periods":{i.id : i.json() for i in self.session_periods.all()},
            "session_periods_order" : list(self.session_periods.all().values_list('id', flat=True)),
            "session_players":{i.id : i.json(False) for i in self.session_players.all()},
            "session_players_order" : list(self.session_players.all().values_list('id', flat=True)),
            "invitation_text" : self.invitation_text,
            "invitation_subject" : self.invitation_subject,
            "world_state" : self.world_state,
            "collaborators" : {str(i.id):i.email for i in self.collaborators.all()},
            "collaborators_order" : list(self.collaborators.all().values_list('id', flat=True)),
            "creator" : self.creator.id,
        }
    
    def json_for_subject(self, session_player):
        '''
        json object for subject screen
        session_player : SessionPlayer() : session player requesting session object
        '''
        
        return{
            "started":self.started,
            "parameter_set":self.parameter_set.get_json_for_subject(),

            "session_players":{i.id : i.json_for_subject(session_player) for i in self.session_players.all()},
            "session_players_order" : list(self.session_players.all().values_list('id', flat=True)),

            "session_periods":{i.id : i.json() for i in self.session_periods.all()},
            "session_periods_order" : list(self.session_periods.all().values_list('id', flat=True)),

            "world_state" : self.world_state,
        }
    
    def json_for_timer(self):
        '''
        return json object for timer update
        '''

        session_players = []

        return{
            "started":self.started,
            "session_players":session_players,
            "session_player_earnings": [i.json_earning() for i in self.session_players.all()]
        }
    
    def json_for_parameter_set(self):
        '''
        return json for parameter set setup.
        '''
        message = {
            "id" : self.id,
            "started": self.started,
        }
    
        return message
        
@receiver(post_delete, sender=Session)
def post_delete_parameterset(sender, instance, *args, **kwargs):
    '''
    use signal to delete associated parameter set
    '''
    if instance.parameter_set:
        instance.parameter_set.delete()

@receiver(post_save, sender=Session)
def post_save_session(sender, instance, created, *args, **kwargs):
    '''
    after session is initialized
    '''
    if created:
        id_string = ''.join(random.choices(string.ascii_lowercase, k=6))

        while Session.objects.filter(id_string=id_string).exists():
            id_string = ''.join(random.choices(string.ascii_lowercase, k=6))

        instance.id_string = id_string
