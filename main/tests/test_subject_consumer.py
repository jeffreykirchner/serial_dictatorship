'''
build test
'''

import logging
import sys
import pytest
import json

from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from asgiref.sync import sync_to_async
from asgiref.sync import async_to_sync

from django.test import TestCase


from main.models import Session
from main.globals import ExperimentMode

from main.routing import websocket_urlpatterns

class TestSubjectConsumer(TestCase):
    fixtures = ['auth_user.json', 'main.json']

    user = None
    session = None
    session_player_1 = None

    def setUp(self):
        sys._called_from_test = True
        logger = logging.getLogger(__name__)

        logger.info('setup tests')

        self.session = Session.objects.filter(title="Sample").first()
        self.assertEqual(self.session.title, "Sample")

    async def set_up_communicators(self, communicator_subject, communicator_staff):
        '''
        setup the socket communicators
        '''
        logger = logging.getLogger(__name__)

        session_player = await self.session.session_players.afirst()

        connection_path_staff = f"/ws/staff-session/{self.session.channel_key}/session-{self.session.id}/{self.session.channel_key}"

        application = URLRouter(websocket_urlpatterns)
        
        #subjects
        async for i in self.session.session_players.all():
            connection_path_subject = f"/ws/subject-home/{self.session.channel_key}/session-{self.session.id}/{i.player_key}"
            communicator_subject.append(WebsocketCommunicator(application, connection_path_subject))

            connected_subject, subprotocol_subject = await communicator_subject[-1].connect()
            assert connected_subject

            communicator_subject[-1].scope["session_player_id"] = i.id

            message = {'message_type': 'get_session',
                       'message_text': {"player_key" :str(i.player_key)}}

            await communicator_subject[-1].send_json_to(message)
            response = await communicator_subject[-1].receive_json_from()
            # logger.info(response)
            
            self.assertEqual(response['message']['message_type'],'get_session')
            self.assertEqual(response['message']['message_data']['session_player']['id'], i.id)

        #staff
        communicator_staff = WebsocketCommunicator(application, connection_path_staff)
        connected_staff, subprotocol_staff = await communicator_staff.connect()
        assert connected_staff

        # #get staff session
        message = {'message_type': 'get_session',
                   'message_text': {"session_key" :str(self.session.session_key)}}

        await communicator_staff.send_json_to(message)
        response = await communicator_staff.receive_json_from()
        #logger.info(response)
        
        self.assertEqual(response['message']['message_type'],'get_session')

        return communicator_subject, communicator_staff

    async def start_session(self, communicator_subject, communicator_staff):
        '''
        start session and advance past instructions
        '''
        logger = logging.getLogger(__name__)
        
        # #start session
        message = {'message_type' : 'start_experiment',
                   'message_text' : {},
                   'message_target' : 'self', }

        await communicator_staff.send_json_to(message)

        response = await communicator_staff.receive_json_from(timeout=10)

        for i in communicator_subject:
            response = await i.receive_json_from(timeout=10)
            self.assertEqual(response['message']['message_type'],'update_start_experiment')
            message_data = response['message']['message_data']
            self.assertEqual(message_data['value'],'success')
        
        # #advance past instructions
        # message = {'message_type' : 'next_phase',
        #            'message_text' : {},
        #            'message_target' : 'self',}

        # await communicator_staff.send_json_to(message)
       
        # for i in communicator_subject:
        #     response = await i.receive_json_from()
        #     self.assertEqual(response['message']['message_type'],'update_next_phase')
        #     message_data = response['message']['message_data']
        #     self.assertEqual(message_data['value'],'success')
           
        # response = await communicator_staff.receive_json_from()

        return communicator_subject, communicator_staff
    
    async def advance_past_chat(self, communicator_subject, communicator_staff):
        '''
        advance past chat
        '''
        logger = logging.getLogger(__name__)

        #advance past chat
        message = {'message_type' : 'done_chatting',
                   'message_text' : {"current_period": 1, "auto_submit": True},
                   'message_target' : 'group',}
        
        for index, i in enumerate(communicator_subject):
            # logger.info(f"submitting done_chatting for {i.scope['session_player_id']}")
            await i.send_json_to(message)

            #staff response

            if index<len(communicator_subject)-1:
                response = await communicator_staff.receive_json_from()
                self.assertEqual(response['message']['message_type'],'update_status')
                message_data = response['message']['message_data']
                self.assertEqual(message_data['status'],'success')
            else:
                #staff response
                response = await communicator_staff.receive_json_from()
                self.assertEqual(response['message']['message_type'],'update_done_chatting')
                message_data = response['message']['message_data']

                #subject response
                for j in communicator_subject:
                    response = await j.receive_json_from()
                    self.assertEqual(response['message']['message_type'],'update_done_chatting')
                    message_data = response['message']['message_data']

    async def submit_choices_simultaneous(self, communicator_subject, communicator_staff):
        '''
        submit choices
        '''
        logger = logging.getLogger(__name__)

        #submit choices
        for index, i in enumerate(communicator_subject):
            # logger.info(f"submitting choice for {i.scope['session_player_id']}")

            message = {"message_type" : "choices_simultaneous",
                       "message_text" : {"choices": [1,2,3,4], "auto_submit": False,},
                       "message_target" : "group"}
            
            #check subject response
            await i.send_json_to(message)

            if index<len(communicator_subject)-1:
                response = await i.receive_json_from()
                message_data = response['message']['message_data']
                self.assertEqual(message_data['status'],'success')

                #check staff response
                response = await communicator_staff.receive_json_from()
                message_data = response['message']['message_data']
                self.assertEqual(message_data['status'],'success')
            else:
                #staff response
                response = await communicator_staff.receive_json_from()
                self.assertEqual(response['message']['message_type'],'update_result')
                message_data = response['message']['message_data']

                #subject response
                for j in communicator_subject:
                    response = await j.receive_json_from()
                    self.assertEqual(response['message']['message_type'],'update_result')
                    message_data = response['message']['message_data']
    
    async def ready_to_go_on(self, communicator_subject, communicator_staff):
        '''
        ready to go on
        '''
        logger = logging.getLogger(__name__)

        #ready to go on
        message = {'message_type' : 'ready_to_go_on',
                   'message_text' : {'auto_submit': False},
                   'message_target' : 'group',}

        for index, i in enumerate(communicator_subject):
            #check subject response
            await i.send_json_to(message)

            if index<len(communicator_subject)-1:
               
                #check staff response
                response = await communicator_staff.receive_json_from()
                message_data = response['message']['message_data']
                self.assertEqual(message_data['status'],'success')
                self.assertEqual(message_data['player_status'],'Waiting')
            else:
                #staff response
                response = await communicator_staff.receive_json_from()
                self.assertEqual(response['message']['message_type'],'update_start_next_period')

                #subject response
                for j in communicator_subject:
                    response = await j.receive_json_from()
                    self.assertEqual(response['message']['message_type'],'update_start_next_period')
                    
    @pytest.mark.asyncio
    async def test_submit_simultanious(self):
        '''
        test submitting submitting simultanious choices
        '''        
        communicator_subject = []
        communicator_staff = None

        logger = logging.getLogger(__name__)
        logger.info(f"called from test {sys._called_from_test}" )

        communicator_subject, communicator_staff = await self.set_up_communicators(communicator_subject, communicator_staff)
        communicator_subject, communicator_staff = await self.start_session(communicator_subject, communicator_staff)

        await communicator_staff.send_json_to({"message_type": "get_world_state_local", "message_text": {}})
        response = await communicator_staff.receive_json_from()
        world_state = response['message']['message_data']

        session = await Session.objects.prefetch_related('parameter_set').aget(id=self.session.id)

        self.assertEqual(world_state['current_experiment_phase'], 'Run')
        self.assertEqual(session.parameter_set.experiment_mode, ExperimentMode.SIMULTANEOUS) 

        #advance past chat
        await self.advance_past_chat(communicator_subject, communicator_staff)

        #send incorrect number of choices
        message = {"message_type" : "choices_simultaneous",
                   "message_text" : {"choices": [1,2,3], "auto_submit": False,},
                   "message_target" : "group"}
        await communicator_subject[0].send_json_to(message)
        response = await communicator_subject[0].receive_json_from()

        message_data = response['message']['message_data']
        self.assertEqual(message_data['status'],'fail')
        self.assertEqual(message_data['error_message'], "Rank all choices.")

        #send invalid sequence of choices
        message = {"message_type" : "choices_simultaneous",
                   "message_text" : {"choices": [1,2,3,5], "auto_submit": False,},
                   "message_target" : "group"}
        await communicator_subject[0].send_json_to(message)
        response = await communicator_subject[0].receive_json_from()

        message_data = response['message']['message_data']
        self.assertEqual(message_data['status'],'fail')
        self.assertEqual(message_data['error_message'], "Choices must be between 1 and 4.")

        #check for no valid characters
        message = {"message_type" : "choices_simultaneous",
                   "message_text" : {"choices": ["a", "b", "c", "d"], "auto_submit": False,},
                   "message_target" : "group"}
        await communicator_subject[0].send_json_to(message)
        response = await communicator_subject[0].receive_json_from()

        message_data = response['message']['message_data']
        self.assertEqual(message_data['status'],'fail')
        self.assertEqual(message_data['error_message'], "Choices must be whole numbers.")

        #check for decimal numbers
        message = {"message_type" : "choices_simultaneous",
                   "message_text" : {"choices": [1.1, 2.2, 3.3, 4.4], "auto_submit": False,},
                   "message_target" : "group"}
        await communicator_subject[0].send_json_to(message)
        response = await communicator_subject[0].receive_json_from()

        message_data = response['message']['message_data']
        self.assertEqual(message_data['status'],'fail')
        self.assertEqual(message_data['error_message'], "Choices must be whole numbers.")

        #submit choices simultaneous
        await self.submit_choices_simultaneous(communicator_subject, communicator_staff)

        #ready to go on
        await self.ready_to_go_on(communicator_subject, communicator_staff)

        #verify world state current period is 2
        await communicator_staff.send_json_to({"message_type": "get_world_state_local", "message_text": {}})
        response = await communicator_staff.receive_json_from()
        world_state = response['message']['message_data']

        self.assertEqual(world_state['current_experiment_phase'], 'Run')
        self.assertEqual(world_state['current_period'], 2)

    @pytest.mark.asyncio
    async def test_submit_simultanious_double_submit(self):
        '''
        test submitting simultanious choices twice fails
        '''

        communicator_subject = []
        communicator_staff = None

        logger = logging.getLogger(__name__)
        logger.info(f"called from test {sys._called_from_test}" )

        communicator_subject, communicator_staff = await self.set_up_communicators(communicator_subject, communicator_staff)
        communicator_subject, communicator_staff = await self.start_session(communicator_subject, communicator_staff)

        await communicator_staff.send_json_to({"message_type": "get_world_state_local", "message_text": {}})
        response = await communicator_staff.receive_json_from()
        world_state = response['message']['message_data']

        session = await Session.objects.prefetch_related('parameter_set').aget(id=self.session.id)

        self.assertEqual(world_state['current_experiment_phase'], 'Run')
        self.assertEqual(session.parameter_set.experiment_mode, ExperimentMode.SIMULTANEOUS)

        #advance past chat
        await self.advance_past_chat(communicator_subject, communicator_staff)

        #subject 0 subjects a valid choice set
        message = {"message_type" : "choices_simultaneous",
                   "message_text" : {"choices": [1,2,3,4], "auto_submit": False,},
                   "message_target" : "group"}
        await communicator_subject[0].send_json_to(message)

        response = await communicator_subject[0].receive_json_from()
        message_data = response['message']['message_data']
        self.assertEqual(message_data['status'],'success')

        #staff response
        response = await communicator_staff.receive_json_from()
        message_data = response['message']['message_data']
        self.assertEqual(message_data['status'],'success')

        #subjecct 0 tries to submit again, no response should be received
        await communicator_subject[0].send_json_to(message)
        response = await communicator_subject[0].receive_nothing()
        self.assertTrue(response, "Subject should not be able to submit choices again.")

        response = await communicator_staff.receive_nothing()
        self.assertTrue(response, "Staff should not receive a response for double submission.")


    async def test_submit_sequential(self):
        '''
        test submitting sequential choices
        '''

        communicator_subject = []
        communicator_staff = None

        logger = logging.getLogger(__name__)
        logger.info(f"called from test {sys._called_from_test}" )

        session = await Session.objects.prefetch_related('parameter_set').aget(id=self.session.id)
        session.parameter_set.experiment_mode = ExperimentMode.SEQUENTIAL
        await session.parameter_set.asave()

        communicator_subject, communicator_staff = await self.set_up_communicators(communicator_subject, communicator_staff)
        communicator_subject, communicator_staff = await self.start_session(communicator_subject, communicator_staff)

        await communicator_staff.send_json_to({"message_type": "get_world_state_local", "message_text": {}})
        response = await communicator_staff.receive_json_from()
        world_state = response['message']['message_data']

        self.assertEqual(world_state['current_experiment_phase'], 'Run')
        self.assertEqual(session.parameter_set.experiment_mode, ExperimentMode.SEQUENTIAL) 
        
            


        
