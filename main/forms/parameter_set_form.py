'''
Parameterset edit form
'''

from django import forms

from main.models import ParameterSet

from main.globals import ExperimentMode
from main.globals import ChatGPTMode

import  main

class ParameterSetForm(forms.ModelForm):
    '''
    Parameterset edit form
    '''
    period_count = forms.IntegerField(label='Number of Periods',
                                      min_value=1,
                                      widget=forms.NumberInput(attrs={"v-model":"parameter_set.period_count",
                                                                      "step":"1",
                                                                      "min":"1"}))

    period_length = forms.IntegerField(label='Period Length (seconds)',
                                       min_value=1,
                                       widget=forms.NumberInput(attrs={"v-model":"parameter_set.period_length",
                                                                       "step":"1",
                                                                       "min":"1"}))
    
    group_size = forms.IntegerField(label='Group Size',
                                      min_value=1,
                                      widget=forms.NumberInput(attrs={"v-model":"parameter_set.group_size",
                                                                     "step":"1",
                                                                     "min":"1"}))

    possible_values = forms.CharField(label='Possible Values',
                                       required=False,
                                       help_text='Comma separated list of possible values, e.g. 0.00,0.25 ...',
                                       widget=forms.TextInput(attrs={"v-model":"parameter_set.possible_values",
                                                                     "placeholder":"1,2,3,4"}))
    
    experiment_mode = forms.ChoiceField(label='Experiment Mode',
                                        choices=ExperimentMode.choices,
                                        widget=forms.Select(attrs={"v-model":"parameter_set.experiment_mode",}))

    max_priority_score = forms.IntegerField(label='Max Priority Score',
                                      min_value=1,
                                      widget=forms.NumberInput(attrs={"v-model":"parameter_set.max_priority_score",
                                                                      "step":"1",
                                                                      "min":"1"}))
    
    chat_gpt_mode = forms.ChoiceField(label='ChatGPT Mode',
                                      choices=ChatGPTMode.choices,
                                      widget=forms.Select(attrs={"v-model":"parameter_set.chat_gpt_mode",}))
    
    chat_gpt_length = forms.IntegerField(label='ChatGPT Length (seconds)',
                                         min_value=1,
                                         widget=forms.NumberInput(attrs={"v-model":"parameter_set.chat_gpt_length",
                                                                         "step":"1",
                                                                         "min":"1"}))


    show_instructions = forms.ChoiceField(label='Show Instructions',
                                          choices=((1, 'Yes'), (0,'No' )),
                                          widget=forms.Select(attrs={"v-model":"parameter_set.show_instructions",}))

    survey_required = forms.ChoiceField(label='Show Survey',
                                        choices=((1, 'Yes'), (0,'No' )),
                                        widget=forms.Select(attrs={"v-model":"parameter_set.survey_required",}))

    survey_link =  forms.CharField(label='Survey Link',
                                   required=False,
                                   widget=forms.TextInput(attrs={"v-model":"parameter_set.survey_link",}))
    
    prolific_mode = forms.ChoiceField(label='Prolific Mode',
                                      choices=((1, 'Yes'), (0,'No' )),
                                      widget=forms.Select(attrs={"v-model":"parameter_set.prolific_mode",}))

    prolific_completion_link =  forms.CharField(label='After Session, Forward Subjects to URL',
                                                required=False,
                                                widget=forms.TextInput(attrs={"v-model":"parameter_set.prolific_completion_link",}))
    
    reconnection_limit = forms.IntegerField(label='Re-connection Limit',
                                            min_value=1,
                                            widget=forms.NumberInput(attrs={"v-model":"parameter_set.reconnection_limit",
                                                                            "step":"1",
                                                                            "min":"1"}))
                                                                
    test_mode = forms.ChoiceField(label='Test Mode',
                                  choices=((1, 'Yes'), (0, 'No')),
                                  widget=forms.Select(attrs={"v-model":"parameter_set.test_mode",}))

    ready_to_go_on_length = forms.IntegerField(label='Ready To Go On Length',
                                               min_value=1,
                                               widget=forms.NumberInput(attrs={"v-model":"parameter_set.ready_to_go_on_length","step":"1","min":"1"}))
   
    class Meta:
        model=ParameterSet
        fields =['period_count', 'period_length', 'ready_to_go_on_length', 'group_size', 'possible_values', 'experiment_mode','max_priority_score',
                 'chat_gpt_mode', 'chat_gpt_length', 'show_instructions', 
                 'survey_required', 'survey_link', 'prolific_mode', 'prolific_completion_link', 'reconnection_limit',
                 'test_mode',  ]

    def clean_survey_link(self):
        
        try:
           survey_link = self.data.get('survey_link')
           survey_required = int(self.data.get('survey_required'))

           if survey_required and (not survey_link or not "http" in survey_link):
               raise forms.ValidationError('Invalid link')
            
        except ValueError:
            raise forms.ValidationError('Invalid Entry')

        return survey_link
    
    def clean_prolific_completion_link(self):
        
        try:
           prolific_completion_link = self.data.get('prolific_completion_link')
           prolific_mode = int(self.data.get('prolific_mode'))

           if prolific_mode and (not prolific_completion_link or not "http" in prolific_completion_link):
               raise forms.ValidationError('Enter Prolific completion URL')
            
        except ValueError:
            raise forms.ValidationError('Invalid Entry')

        return prolific_completion_link

    def clean_possible_values(self):
        #number of possible values must be greater than or equal to the group size
        try:
            possible_values = self.data.get('possible_values')
            group_size = int(self.data.get('group_size', 1))
            if possible_values:
                values = [float(v.strip()) for v in possible_values.split(',')]
                if len(values) < group_size:
                    raise forms.ValidationError('The number of possible values must be greater than or equal to the group size')
                
                #return csv string of values
                values = [str(v) for v in values]
                return ','.join(values)
            else:
                raise forms.ValidationError('Invalid Entry, use comma separated numbers')
        except ValueError:
            raise forms.ValidationError('Invalid Entry, use comma separated numbers')
