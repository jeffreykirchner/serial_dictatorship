'''
parameterset group period
'''

from django.db import models
from django.core.serializers.json import DjangoJSONEncoder

from main.models import ParameterSetGroup

import main

class ParameterSetGroupPeriod(models.Model):
    '''
    parameter set group period
    '''

    parameter_set_group = models.ForeignKey(ParameterSetGroup, on_delete=models.CASCADE, related_name="parameter_set_groups")

    period_number = models.PositiveIntegerField(default=1, blank=True, null=True)
    values = models.JSONField(default=dict, blank=True, null=True, encoder=DjangoJSONEncoder)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    updated= models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Parameter Set Group Period'
        verbose_name_plural = 'Parameter Set Group Periods'
        ordering = ['period_number']
        
    def from_dict(self, new_ps):
        '''
        copy source values into this period
        source : dict object of parameterset player
        '''       
        
        self.period_number = new_ps.get("period_number", 1)
        self.values = new_ps.get("values", {})
        
        self.save()
        
        message = "Parameters loaded successfully."

        return message
    
    def setup(self):
        '''
        default setup
        '''    
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
            "values" : self.values if self.values else {},

        }
    
    def get_json_for_subject(self, update_required=False):
        '''
        return json object for subject screen, return cached version if unchanged
        '''

        return self.json()


