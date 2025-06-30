'''
instruction form admin screen
'''
from django import forms
from main.models import InstructionSet
from tinymce.widgets import TinyMCE

class InstructionSetFormAdmin(forms.ModelForm):
    '''
    instruction set form admin screen
    '''

    label = forms.CharField(label='Instruction Set Name',
                            widget=forms.TextInput(attrs={"width":"300px"}))
    
    action_page_1 = forms.IntegerField(label='Required Action: 1', initial=1, widget=forms.NumberInput(attrs={"min":"1", "placeholder" : "Page Number"}))
    action_page_2 = forms.IntegerField(label='Required Action: 2', initial=2, widget=forms.NumberInput(attrs={"min":"1", "placeholder" : "Page Number"}))
    action_page_3 = forms.IntegerField(label='Required Action: 3', initial=3, widget=forms.NumberInput(attrs={"min":"1", "placeholder" : "Page Number"}))
    action_page_4 = forms.IntegerField(label='Required Action: 4', initial=4, widget=forms.NumberInput(attrs={"min":"1", "placeholder" : "Page Number"}))
    action_page_5 = forms.IntegerField(label='Required Action: 5', initial=5, widget=forms.NumberInput(attrs={"min":"1", "placeholder" : "Page Number"}))
    action_page_6 = forms.IntegerField(label='Required Action: 6', initial=6, widget=forms.NumberInput(attrs={"min":"1", "placeholder" : "Page Number"}))

    example_values = forms.CharField(label='Example Values',
                                      required=False,
                                      help_text='Comma separated list of example values, e.g. 0.00,0.25,0.50,0.75',
                                      widget=forms.TextInput(attrs={"placeholder":"1,2,3,4"}))
    
    example_prize = forms.DecimalField(label='Example Prize',
                                       max_digits=4,
                                       decimal_places=2,
                                       initial=0.50,
                                       widget=forms.NumberInput(attrs={"step":"0.01", "min":"0.00", "placeholder" : "0.50"}))

    class Meta:
        model=InstructionSet
        fields = ('label', 'action_page_1', 'action_page_2', 'action_page_3', 'action_page_4', 'action_page_5', 'action_page_6')