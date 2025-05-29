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

    priority_scores = forms.CharField(label='Priority Scores',
                                      help_text="Comma-separated integer values assigned based on index. Higher is better, e.g., '5,8,10,1'",
                                      required=False,
                                      widget=forms.TextInput(attrs={"v-model":"current_parameter_set_group_period.priority_scores",
                                                                    "autocomplete":"off",}))

    class Meta:
        model=ParameterSetGroupPeriod
        fields =['values','priority_scores']

