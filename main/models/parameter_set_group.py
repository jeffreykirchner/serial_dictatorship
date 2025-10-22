'''
parameterset group 
'''

from django.db import models
from django.core.serializers.json import DjangoJSONEncoder

from main.models import ParameterSet

import main

class ParameterSetGroup(models.Model):
    '''
    parameter set group
    '''

    parameter_set = models.ForeignKey(ParameterSet, on_delete=models.CASCADE, related_name="parameter_set_groups")

    name = models.CharField(default="Name Here", max_length=255, blank=True, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    updated= models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Parameter Set Group'
        verbose_name_plural = 'Parameter Set Groups'
        ordering = ['name']

    def from_dict(self, new_ps):
        '''
        copy source values into this period
        source : dict object of parameterset player
        '''       
        
        self.name = new_ps.get("name")

        self.save()
        
        message = "Parameters loaded successfully."

        return message
    
    def setup(self):
        '''
        default setup
        '''    
        self.save()

    def update_parameter_set_group_periods(self, repeat_after_period):
        '''
        update parameter set group periods
        '''
        from main.models import ParameterSetGroupPeriod

        period_count = self.parameter_set.period_count

        if period_count> self.parameter_set_group_periods.count():
            # create new periods if needed
            for i in range(self.parameter_set_group_periods.count(), period_count):
                period = ParameterSetGroupPeriod(parameter_set_group=self, period_number=i+1)
                period.save()
                period.setup(repeat_after_period)
        else:
            # remove excess periods
            for period in self.parameter_set_group_periods.order_by('-period_number'):
                if period.period_number > period_count:
                    period.delete()

    def update_json_local(self):
        '''
        update parameter set json
        '''
        self.parameter_set.json_for_session["parameter_set_groups"][self.id] = self.json()

        self.parameter_set.save()

        self.save()

    def json(self):
        '''
        return json object of model
        '''
        
        return{

            "id" : self.id,
            "name" : self.name,

        }
    
    def get_json_for_subject(self, update_required=False):
        '''
        return json object for subject screen, return cached version if unchanged
        '''

        return self.json()


