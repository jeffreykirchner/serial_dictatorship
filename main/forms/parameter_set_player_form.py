'''
parameterset player edit form
'''

from django import forms

from main.models import ParameterSetGroup
from main.models import ParameterSetPlayer
from main.models import InstructionSet

class ParameterSetPlayerForm(forms.ModelForm):
    '''
    parameterset player edit form
    '''
    
    parameter_set_group = forms.ModelChoiceField(label='Group',
                                                 queryset=ParameterSetGroup.objects.none(),
                                                 widget=forms.Select(attrs={"v-model":"current_parameter_set_player.parameter_set_group",}))
    
    group_index = forms.IntegerField(label='Group Index',
                                     help_text='ID within the group',
                                     min_value=1,
                                     widget=forms.NumberInput(attrs={"v-model":"current_parameter_set_player.group_index",}))  
      
    instruction_set = forms.ModelChoiceField(label='instruction_set',
                                             empty_label=None,
                                             queryset=InstructionSet.objects.all(),
                                             widget=forms.Select(attrs={"v-model":"current_parameter_set_player.instruction_set",}))

    class Meta:
        model=ParameterSetPlayer
        fields =['parameter_set_group', 'group_index', 'instruction_set']
    
