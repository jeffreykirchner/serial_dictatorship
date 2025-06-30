'''
instruction set form
'''
from django import forms
from main.models import InstructionSet

class InstructionSetForm(forms.ModelForm):
    '''
    instruction set form 
    '''

    label = forms.CharField(label='Instruction Set Name',
                            widget=forms.TextInput(attrs={"width":"300px",
                                                          "v-model":"instruction_set.label",
                                                          "placeholder" : "Instruction Set Name"}))
    
    action_page_1 = forms.IntegerField(label='Required Action: Submit Choice', 
                                       widget=forms.NumberInput(attrs={"min":"1", 
                                                                       "v-model":"instruction_set.action_page_1",
                                                                       "placeholder" : "Page Number"}))
    
    action_page_2 = forms.IntegerField(label='Required Action: Chat Bot', 
                                       widget=forms.NumberInput(attrs={"min":"1", 
                                                                        "v-model":"instruction_set.action_page_2",
                                                                       "placeholder" : "Page Number"}))
    
    action_page_3 = forms.IntegerField(label='Required Action: 3', 
                                       widget=forms.NumberInput(attrs={"min":"1", 
                                                                       "v-model":"instruction_set.action_page_3",
                                                                       "placeholder" : "Page Number"}))
    
    action_page_4 = forms.IntegerField(label='Required Action: 4', 
                                       widget=forms.NumberInput(attrs={"min":"1", 
                                                                       "v-model":"instruction_set.action_page_4",
                                                                       "placeholder" : "Page Number"}))
    
    action_page_5 = forms.IntegerField(label='Required Action: 5', 
                                       widget=forms.NumberInput(attrs={"min":"1", 
                                                                       "v-model":"instruction_set.action_page_5",
                                                                       "placeholder" : "Page Number"}))
    
    action_page_6 = forms.IntegerField(label='Required Action: 6', 
                                       widget=forms.NumberInput(attrs={"min":"1", 
                                                                       "v-model":"instruction_set.action_page_6",
                                                                       "placeholder" : "Page Number"}))
    
    example_values = forms.CharField(label='Example Values',
                                     help_text='Comma separated list of example values, e.g. 0.00,0.25,0.50,0.75',
                                     widget=forms.TextInput(attrs={"v-model":"instruction_set.example_values",
                                                                   "placeholder":"1,2,3,4"}))
    
    example_prize = forms.DecimalField(label='Example Prize',
                                        max_digits=4,
                                        decimal_places=2,
                                        initial=0.50,
                                        widget=forms.NumberInput(attrs={"step":"0.01",
                                                                       "min":"0.00",
                                                                       "v-model":"instruction_set.example_prize",
                                                                       "placeholder" : "0.50"}))

    class Meta:
        model=InstructionSet
        fields = ('label', 'action_page_1', 'action_page_2', 'action_page_3', 'action_page_4', 'action_page_5', 'action_page_6', 'example_values', 'example_prize')

    def clean_example_values(self):
        #number of possible values must be greater than or equal to the group size
        try:
            example_values = self.data.get('example_values')

            if example_values:
                values = [float(v.strip()) for v in example_values.split(',')]
                if len(values) < 1:
                    raise forms.ValidationError('The number of example values must be greater than or equal to 1')

                #return csv string of values
                values = [str(v) for v in values]
                return ','.join(values)
            else:
                raise forms.ValidationError('Invalid Entry, use comma separated numbers')
        except ValueError:
            raise forms.ValidationError('Invalid Entry, use comma separated numbers')