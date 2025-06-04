'''
gloabal functions related to parameter sets
'''

from django.db import models
from django.utils.translation import gettext_lazy as _

import main

class ChatTypes(models.TextChoices):
    '''
    chat types
    '''
    ALL = 'All', _('All')
    INDIVIDUAL = 'Individual', _('Individual')

class ExperimentPhase(models.TextChoices):
    '''
    experiment phases
    '''
    INSTRUCTIONS = 'Instructions', _('Instructions')
    RUN = 'Run', _('Run')
    NAMES = 'Names', _('Names')
    DONE = 'Done', _('Done')

class ExperimentMode(models.TextChoices):
    '''
    experiment modes
    '''
    SIMULTANEOUS = 'Simultaneous', _('Simultaneous')
    SEQUENTIAL = 'Sequential', _('Sequential')

class SubjectStatus(models.TextChoices):
    '''
    subject status
    '''
    RANKING = 'Ranking', _('Ranking')
    FINISHED_RANKING = 'Finished_Ranking', _('Finished_Ranking')
    REVIEWING_RESULTS = 'Reviewing_Results', _('Reviewing_Results')
    WAITING = 'Waiting', _('Waiting')

class ChatGPTMode(models.TextChoices):
    '''
    chat gpt modes
    '''
    OFF = 'Off', _('Off')
    WITH_CONTEXT = 'With Context', _('With Context')
    WITHOUT_CONTEXT = 'Without Context', _('Without Context')
