'''
parameterset group period
'''
import random

from django.db import models
from django.core.serializers.json import DjangoJSONEncoder

from main.models import ParameterSetGroup

import main

class ParameterSetGroupPeriod(models.Model):
    '''
    parameter set group period
    '''

    parameter_set_group = models.ForeignKey(ParameterSetGroup, on_delete=models.CASCADE, related_name="parameter_set_group_periods")

    period_number = models.PositiveIntegerField(default=1, blank=True, null=True)
    values = models.CharField("0.00,0.25,0.75,1.00", max_length=1000, blank=True, null=True)
    priority_scores = models.CharField("2,3,4,5", max_length=1000, blank=True, null=True)
    player_order = models.CharField("1,2,3,4", max_length=1000, blank=True, null=True)

    timestamp = models.DateTimeField(auto_now_add=True)
    updated= models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Parameter Set Group Period'
        verbose_name_plural = 'Parameter Set Group Periods'
        ordering = ['parameter_set_group__name', 'period_number']
        
    def from_dict(self, new_ps):
        '''
        copy source values into this period
        source : dict object of parameterset player
        '''       
        
        self.period_number = new_ps.get("period_number", 1)
        self.values = new_ps.get("values", {1,2,3,4})
        self.priority_scores = new_ps.get("priority_scores", "1,2,3,4")
        self.player_order = new_ps.get("player_order", "1,2,3,4")
        
        self.save()
        
        message = "Parameters loaded successfully."

        return message
    
    def setup(self, repeat_after_period=None):
        '''
        default setup
        '''
        possible_values = self.parameter_set_group.parameter_set.possible_values.split(",")
        for i in possible_values:
            i = i.strip()

        self.values = ""

        if repeat_after_period and self.period_number > repeat_after_period:
            # repeat values from earlier period
            source_period_number = self.period_number - repeat_after_period
     
            source_period = self.parameter_set_group.parameter_set_group_periods.get(period_number=source_period_number)
            self.values = source_period.values
            self.priority_scores = source_period.priority_scores
            self.player_order = source_period.player_order

        else:
            #randomly assign values from possible values
            for i in range(self.parameter_set_group.parameter_set.group_size):
                index = random.randint(0, len(possible_values) - 1)

                if self.values == "":
                    self.values = possible_values[index]
                else:
                    self.values += "," + possible_values[index]
            
                possible_values.pop(index)
            
            #randomly assign priority scores       
            self.priority_scores = ""
            for i in range(self.parameter_set_group.parameter_set.group_size):
                score = random.randint(1, self.parameter_set_group.parameter_set.max_priority_score)
                if self.priority_scores == "":
                    self.priority_scores = str(score)
                else:
                    self.priority_scores += "," + str(score)
            
            #assign player order based on priority scores, with highest score first, ties broken by random order
            if self.priority_scores:
                scores = list(map(int, self.priority_scores.split(",")))
                order = sorted(range(len(scores)), key=lambda k: (-scores[k], random.random()))
                self.player_order = ",".join(str(i + 1) for i in order)
            else:
                self.player_order = ",".join(str(i + 1) for i in range(self.parameter_set_group.parameter_set.group_size))

        
        self.save()
    
    def update_json_local(self):
        '''
        update parameter set json
        '''
        self.parameter_set.json_for_session["parameter_set_group_periods"][self.id] = self.json()

        self.parameter_set.save()

        self.save()

    def json(self):
        '''
        return json object of model
        '''
        
        return{

            "id" : self.id,
            "parameter_set_group" : self.parameter_set_group.id if self.parameter_set_group else None,
            "period_number" : self.period_number,
            "values" : self.values if self.values else None,
            "priority_scores" : self.priority_scores if self.priority_scores else None,
            "player_order" : self.player_order if self.player_order else None,
        }
    
    def get_json_for_subject(self, update_required=False):
        '''
        return json object for subject screen, return cached version if unchanged
        '''

        return self.json()


