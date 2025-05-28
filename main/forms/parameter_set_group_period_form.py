'''
parameterset group edit form
'''

from django import forms

from main.models import ParameterSetGroupPeriod

class ParameterSetGroupPeriodForm(forms.ModelForm):
    '''
    parameterset field type edit form
    '''
    
    values = forms.CharField(label='Values',
                             help_text="Comma-separated values, e.g., '0.00,0.25...'",
                             widget=forms.TextInput(attrs={"v-model":"current_parameter_set_group_period.values",
                                                           "autocomplete":"off",}))

    class Meta:
        model=ParameterSetGroupPeriod
        fields =['values',]
    
