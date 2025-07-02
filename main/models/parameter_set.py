'''
parameter set
'''
import logging
import json

from decimal import Decimal

from django.db import models
from django.db.utils import IntegrityError
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ObjectDoesNotExist

from main.models import InstructionSet

from main.globals import ExperimentMode
from main.globals import ChatGPTMode

import main

class ParameterSet(models.Model):
    '''
    parameter set
    '''    
    period_count = models.IntegerField(verbose_name='Number of periods', default=20)                          #number of periods in the experiment
    period_length = models.IntegerField(verbose_name='Period Length, Production', default=60)                 #period length in seconds
    ready_to_go_on_length = models.IntegerField(verbose_name='Ready To Go On Length', default=30)             #length subject has to press ready to go on button
    group_size = models.IntegerField(verbose_name='Group Size', default=4)                                    #number of players in a group
    possible_values = models.CharField(max_length=1000, default='0.00,0.25,0.50,0.75,1.00,1.25', verbose_name='Possible Values', blank=True, null=True) #possible values for the game
    experiment_mode = models.CharField(max_length=20, choices=ExperimentMode.choices, default=ExperimentMode.SIMULTANEOUS, verbose_name='Experiment Mode') #experiment mode, simultaneous or sequential
    max_priority_score = models.IntegerField(verbose_name='Max Priority Score', default=10)
    chat_gpt_mode = models.CharField(max_length=20, choices=ChatGPTMode.choices, default=ChatGPTMode.OFF, verbose_name='ChatGPT Mode')
    chat_gpt_length = models.IntegerField(verbose_name='ChatGPT Length', default=60)                       #length of time a user can interact with chat gpt each period.

    show_instructions = models.BooleanField(default=True, verbose_name='Show Instructions')                   #if true show instructions

    survey_required = models.BooleanField(default=False, verbose_name="Survey Required")                      #if true show the survey below
    survey_link = models.CharField(max_length = 1000, default = '', verbose_name = 'Survey Link', blank=True, null=True)

    prolific_mode = models.BooleanField(default=False, verbose_name="Prolific Mode")                          #put study into prolific mode
    prolific_completion_link = models.CharField(max_length = 1000, default = '', verbose_name = 'Forward to Prolific after sesison', blank=True, null=True) #at the completion of the study forward subjects to link

    reconnection_limit = models.IntegerField(verbose_name='Limit Subject Screen Reconnection Trys', default=25)       #limit subject screen reconnection trys

    test_mode = models.BooleanField(default=False, verbose_name='Test Mode')                                #if true subject screens will do random auto testing

    json_for_session = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)                   #json model of parameter set 

    timestamp = models.DateTimeField(auto_now_add=True)
    updated= models.DateTimeField(auto_now=True)

    

    def __str__(self):
        return self.session.title

    class Meta:
        verbose_name = 'Parameter Set'
        verbose_name_plural = 'Parameter Sets'
    
    def from_dict(self, new_ps):
        '''
        load values from dict
        '''
        logger = logging.getLogger(__name__) 

        message = "Parameters loaded successfully."
        status = "success"

        try:
            self.period_count = new_ps.get("period_count")
            self.period_length = new_ps.get("period_length")
            self.ready_to_go_on_length = new_ps.get("ready_to_go_on_length", 30)
            self.group_size = new_ps.get("group_size", 4)
            self.possible_values = new_ps.get("possible_values", "0.00,0.25,0.50,0.75,1.00,1.25")
            self.experiment_mode = new_ps.get("experiment_mode", ExperimentMode.SIMULTANEOUS)
            self.max_priority_score = new_ps.get("max_priority_score", 1)
            self.chat_gpt_mode = new_ps.get("chat_gpt_mode", ChatGPTMode.OFF)
            self.chat_gpt_length = new_ps.get("chat_gpt_length", 60)

            self.show_instructions = True if new_ps.get("show_instructions") else False

            self.survey_required = True if new_ps.get("survey_required") else False
            self.survey_link = new_ps.get("survey_link")

            self.prolific_mode = True if new_ps.get("prolific_mode", False) else False
            self.prolific_completion_link = new_ps.get("prolific_completion_link", None)

            self.reconnection_limit = new_ps.get("reconnection_limit", None)

            self.save()

            #parameter set groups
            self.parameter_set_groups.all().delete()
            new_parameter_set_groups = new_ps.get("parameter_set_groups")
            new_parameter_set_groups_map = {}

            for i in new_parameter_set_groups:
                p = main.models.ParameterSetGroup.objects.create(parameter_set=self)
                v = new_parameter_set_groups[i]
                p.from_dict(v)

                new_parameter_set_groups_map[i] = p.id

            #update parameter set group periods
            main.models.ParameterSetGroupPeriod.objects.filter(parameter_set_group__parameter_set=self).delete()
            new_parameter_set_group_periods = new_ps.get("parameter_set_group_periods")
            for i in new_parameter_set_group_periods:
                v = new_parameter_set_group_periods[i]
                p = main.models.ParameterSetGroupPeriod.objects.create(parameter_set_group_id=new_parameter_set_groups_map[str(v["parameter_set_group"])])
                p.from_dict(v)

            #parameter set players
            self.parameter_set_players.all().delete()

            new_parameter_set_players = new_ps.get("parameter_set_players")

            for i in new_parameter_set_players:
                p = main.models.ParameterSetPlayer.objects.create(parameter_set=self)
                v = new_parameter_set_players[i]
                p.from_dict(new_parameter_set_players[i])

                if v.get("parameter_set_group", None) != None:
                    p.parameter_set_group_id=new_parameter_set_groups_map[str(v["parameter_set_group"])]

                if v.get("instruction_set", None) != None:
                    p.instruction_set = InstructionSet.objects.filter(label=v.get("instruction_set_label",None)).first()
                
                p.save()

            self.update_player_count()

            #parameter set notices
            self.parameter_set_notices.all().delete()
            new_parameter_set_notices = new_ps.get("parameter_set_notices")

            for i in new_parameter_set_notices:
                p = main.models.ParameterSetNotice.objects.create(parameter_set=self)
                p.from_dict(new_parameter_set_notices[i])

            self.json_for_session = None
            self.save()
            
        except IntegrityError as exp:
            message = f"Failed to load parameter set: {exp}"
            status = "fail"
            logger.warning(message)

        return {"status" : status, "message" :  message}

    def setup(self):
        '''
        default setup
        '''    
        self.json_for_session = None

        self.save()

        for i in self.parameter_set_players.all():
            i.setup()

        self.json(update_required=True)

    def add_player(self):
        '''
        add a parameterset player
        '''

        player = main.models.ParameterSetPlayer()
        player.parameter_set = self
        player.player_number = self.parameter_set_players.count() + 1

        player.save()

        self.update_json_fk(update_players=True)
    
    def remove_player(self, parameterset_player_id):
        '''
        remove specified parameterset player
        '''
        
        try:
            player = self.parameter_set_players.get(id=parameterset_player_id)
            player.delete()

        except ObjectDoesNotExist:
            logger = logging.getLogger(__name__) 
            logger.warning(f"parameter set remove_player, not found ID: {parameterset_player_id}")

        self.update_player_count()
        self.update_json_fk(update_players=True)
    
    def update_player_count(self):
        '''
        update the number of parameterset players
        '''
        for count, i in enumerate(self.parameter_set_players.all()):
            i.player_number = count + 1
            i.update_json_local()
            i.save()
    
    def update_json_local(self):
        '''
        update json model
        '''
        self.json_for_session["id"] = self.id
                
        self.json_for_session["period_count"] = self.period_count
        self.json_for_session["period_length"] = self.period_length
        self.json_for_session["ready_to_go_on_length"] = self.ready_to_go_on_length
        self.json_for_session["group_size"] = self.group_size
        self.json_for_session["possible_values"] = self.possible_values
        self.json_for_session["experiment_mode"] = self.experiment_mode
        self.json_for_session["max_priority_score"] = self.max_priority_score
        self.json_for_session["chat_gpt_mode"] = self.chat_gpt_mode
        self.json_for_session["chat_gpt_length"] = self.chat_gpt_length

        self.json_for_session["show_instructions"] = 1 if self.show_instructions else 0

        self.json_for_session["survey_required"] = 1 if self.survey_required else 0
        self.json_for_session["survey_link"] = self.survey_link

        self.json_for_session["prolific_mode"] = 1 if self.prolific_mode else 0
        self.json_for_session["prolific_completion_link"] = self.prolific_completion_link

        self.json_for_session["reconnection_limit"] = self.reconnection_limit

        self.json_for_session["test_mode"] = 1 if self.test_mode else 0

        self.save()
    
    def update_json_fk(self, update_players=False, 
                             update_notices=False, 
                             update_groups=False,
                             update_group_periods=False):
        '''
        update json model
        '''
        if update_players:
            self.json_for_session["parameter_set_players_order"] = list(self.parameter_set_players.all().values_list('id', flat=True))
            self.json_for_session["parameter_set_players"] = {p.id : p.json() for p in self.parameter_set_players.all()}

        if update_notices:
            self.json_for_session["parameter_set_notices_order"] = list(self.parameter_set_notices.all().values_list('id', flat=True))
            self.json_for_session["parameter_set_notices"] = {str(p.id) : p.json() for p in self.parameter_set_notices.all()}    

        if update_groups:
            self.json_for_session["parameter_set_groups_order"] = list(self.parameter_set_groups.all().values_list('id', flat=True))
            self.json_for_session["parameter_set_groups"] = {str(p.id) : p.json() for p in self.parameter_set_groups.all()}

        if update_group_periods:
            self.json_for_session["parameter_set_group_periods_order"] = list(main.models.ParameterSetGroupPeriod.objects.filter(parameter_set_group__parameter_set=self).values_list('id', flat=True))
            self.json_for_session["parameter_set_group_periods"] = {str(p.id) : p.json() for p in main.models.ParameterSetGroupPeriod.objects.filter(parameter_set_group__parameter_set=self)}

        self.save()

    def json(self, update_required=False):
        '''
        return json object of model, return cached version if unchanged
        '''
        if not self.json_for_session or \
           update_required:
            self.json_for_session = {}
            self.update_json_local()
            self.update_json_fk(update_players=True, 
                                update_notices=True,
                                update_groups=True,
                                update_group_periods=True)

        return self.json_for_session
    
    def get_json_for_subject(self):
        '''
        return json object for subject, return cached version if unchanged
        '''
        
        if not self.json_for_session:
            return None

        v = self.json_for_session
        
        return v


