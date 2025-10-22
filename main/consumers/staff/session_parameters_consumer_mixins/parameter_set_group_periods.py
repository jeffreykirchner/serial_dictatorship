import logging

from asgiref.sync import sync_to_async

from django.core.exceptions import ObjectDoesNotExist

from main.models import Session
from main.models import ParameterSetGroup
from main.models import ParameterSetGroupPeriod

from main.forms import ParameterSetGroupPeriodForm

from ..session_parameters_consumer_mixins.get_parameter_set import take_get_parameter_set

class ParameterSetGroupPeriodsMixin():
    '''
    parameter set group mixin
    '''

    async def update_parameter_set_group_period(self, event):
        '''
        update a parameterset group
        '''

        message_data = {}
        message_data["status"] = await take_update_parameter_set_group_period(event["message_text"])
        message_data["parameter_set"] = await take_get_parameter_set(event["message_text"]["session_id"])

        await self.send_message(message_to_self=message_data, message_to_group=None,
                                message_type="update_parameter_set", send_to_client=True, send_to_group=False)
    
    async def auto_fill_parameter_set_group_periods(self, event):
        '''
        add a parameterset group
        '''

        message_data = {}
        message_data["status"] = await take_auto_fill_parameter_set_group_periods(event["message_text"])
        message_data["parameter_set"] = await take_get_parameter_set(event["message_text"]["session_id"])

        await self.send_message(message_to_self=message_data, message_to_group=None,
                                message_type="update_parameter_set", send_to_client=True, send_to_group=False)

@sync_to_async
def take_update_parameter_set_group_period(data):
    '''
    update parameterset group
    '''   
    logger = logging.getLogger(__name__) 
    # logger.info(f"Update parameterset group: {data}")

    session_id = data["session_id"]
    parameterset_group_period_id = data["parameterset_group_period_id"]
    form_data = data["form_data"]

    try:        
        session = Session.objects.get(id=session_id)
        parameter_set_group_period = ParameterSetGroupPeriod.objects.get(id=parameterset_group_period_id)
    except ObjectDoesNotExist:
        logger.warning(f"take_update_parameter_set_group_periods, not found ID: {parameterset_group_period_id}")
        return {"value" : "fail"}
    
    form_data_dict = form_data

    # logger.info(f'form_data_dict : {form_data_dict}')

    form = ParameterSetGroupPeriodForm(form_data_dict, instance=parameter_set_group_period)
    
    if form.is_valid():         
        form.save()              
        session.parameter_set.update_json_fk(update_group_periods=True)

        return {"value" : "success"}                      
                                
    logger.warning("Invalid parameterset group form")
    return {"value" : "fail", "errors" : dict(form.errors.items())}

@sync_to_async
def take_auto_fill_parameter_set_group_periods(data):
    '''
    add a new parameter group to the parameter set
    '''
    logger = logging.getLogger(__name__) 
    # logger.info(f"Add parameterset group: {data}")

    session_id = data["session_id"]
    repeat_after_period = data["repeat_after_period"]

    try:        
        session = Session.objects.get(id=session_id)
    except ObjectDoesNotExist:
        logger.warning(f"take_auto_fill_parameter_set_group_periods session, not found ID: {session_id}")
        return {"value" : "fail"}

    #remove all existing group periods
    ParameterSetGroupPeriod.objects.filter(parameter_set_group__parameter_set=session.parameter_set).delete()

    #create new group periods
    for i in session.parameter_set.parameter_set_groups.all():
        i.update_parameter_set_group_periods(repeat_after_period=repeat_after_period)
        
    session.parameter_set.update_json_fk(update_group_periods=True)

    return {"value" : "success"}
    