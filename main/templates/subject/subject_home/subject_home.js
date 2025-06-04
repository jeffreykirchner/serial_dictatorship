
{% load static %}

"use strict";

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

//global letiables
let pixi_notices = {container:null, notices:{}};                         //notices
let pixi_notices_key = 0;

let last_location_update = Date.now();          //last time location was updated

//prevent right click
document.addEventListener('contextmenu', event => event.preventDefault());

let worker = null;

//vue app
let app = Vue.createApp({
    delimiters: ["[[", "]]"],

    data() {return {chat_socket : "",
                    reconnecting : true,
                    help_text : "Loading ...",
                    is_subject : true,
                    working : false,
                    reconnection_count : 0,
                    first_load_done : false,                       //true after software is loaded for the first time
                    player_key : "{{session_player.player_key}}",
                    session_player : null, 
                    session : null,
                    website_instance_id : "{{website_instance_id}}",

                    form_ids: {{form_ids|safe}},

                    end_game_modal_visible : false,

                    instructions : {{instructions|safe}},
                    instruction_pages_show_scroll : false,

                    notices_seen: [],

                    choices : [],
                    choices_error_message : null,
                    // waiting_for_others : false, //true if waiting for other players to make choices

                    // modals
                    end_game_modal : null,
                    help_modal : null,
                    test_mode : {%if session.parameter_set.test_mode%}true{%else%}false{%endif%},        
                    
                    //tick tock
                    tick_tock : "tick",
                    tick_tock_interval : 300,

                    //chat gpt
                    chat_text : "",
                    chat_history : {{session_player.get_chat_display_history|safe}},
                    chat_button_text : 'Chat <i class="far fa-comments"></i>',
                }},
    methods: {

        /** fire when websocket connects to server
        */
        handle_socket_connected: function handle_socket_connected(){            
            app.send_get_session();
            app.working = false;
        },

        /** fire trys to connect to server
         * return true if re-connect should be allowed else false
        */
        handle_socket_connection_try: function handle_socket_connection_try(){            
            if(!app.session) return true;

            app.reconnection_count+=1;

            if(app.reconnection_count > app.session.parameter_set.reconnection_limit)
            {
                app.reconnection_failed = true;
                app.check_in_error_message = "Refresh your browser."
                return false;
            }

            return true;
        },

        /**
         * run tick tock at a set interval
         */
        run_tick_tock: function run_tick_tock() {
            if(app.tick_tock == "tick")
            {
                app.tick_tock = "tock";
            }
            else
            {
                app.tick_tock = "tick";
            }

            setTimeout(app.run_tick_tock, app.tick_tock_interval);
        },

        /** take websocket message from server
        *    @param data {json} incoming data from server, contains message and message type
        */
        take_message: function take_message(data) {

            {%if DEBUG%}
            console.log(data);
            {%endif%}

            let message_type = data.message.message_type;
            let message_data = data.message.message_data;

            switch(message_type) {                
                case "get_session":
                    app.take_get_session(message_data);
                    break; 
                case "help_doc_subject":
                    app.take_load_help_doc_subject(message_data);
                    break;
                case "update_start_experiment":
                    app.take_update_start_experiment(message_data);
                    break;
                case "update_reset_experiment":
                    app.take_reset_experiment(message_data);
                    break;               
                case "update_time":
                    app.take_update_time(message_data);
                    break;
                case "name":
                    app.take_name(message_data);
                    break;
                case "update_next_phase":
                    app.take_update_next_phase(message_data);
                    break;
                case "next_instruction":
                    app.take_next_instruction(message_data);
                    break;
                case "finish_instructions":
                    app.take_finish_instructions(message_data);
                    break;
                case "update_refresh_screens":
                    app.take_refresh_screens(message_data);
                    break;               
                case "update_result":
                    app.take_results(message_data);
                    break;
                case "update_start_next_period":
                    app.take_start_next_period(message_data);
                    break;
                case "update_choices":
                    app.take_choices(message_data);
                    break;
                case "update_show_name_input":
                    app.take_show_name_input(message_data);
                    break;
                case "process_chat_gpt_prompt":
                    app.take_process_chat_gpt_prompt(message_data);
                    break;
            }

            app.first_load_done = true;
            // app.working = false;
        },

        /** send websocket message to server
        *    @param message_type {string} type of message sent to server
        *    @param message_text {json} body of message being sent to server
        */
        send_message: function send_message(message_type, message_text, message_target="self")
        {          
            app.chat_socket.send(JSON.stringify({
                    'message_type': message_type,
                    'message_text': message_text,
                    'message_target': message_target,
                }));
        },

        /**
         * do after session has loaded
        */
        do_first_load: function do_first_load()
        {           
            app.end_game_modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('end_game_modal'), {keyboard: false})   
           
            app.help_modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('help_modal'), {keyboard: false})
            
            document.getElementById('end_game_modal').addEventListener('hidden.bs.modal', app.hide_end_game_modal);

            {%if session.parameter_set.test_mode%} setTimeout(app.do_test_mode, app.random_number(1000 , 1500)); {%endif%}

            // if game is finished show modal
            if( app.session.world_state.current_experiment_phase == 'Names')
            {
                app.show_end_game_modal();
            }
            else if(app.session.world_state.current_experiment_phase == 'Done' && 
                    app.session.parameter_set.survey_required && 
                    !app.session_player.survey_complete)
            {
                window.location.replace(app.session_player.survey_link);
            }

            if(document.getElementById('instructions_frame_a'))
            {
                document.getElementById('instructions_frame_a').addEventListener('scroll',
                    function()
                    {
                        app.scroll_update();
                    },
                    false
                )

                app.scroll_update();
            }

            //load current ranks
            if(app.session.started)
            {
                if(app.session.world_state.session_players[app.session_player.id].status != 'Ranking')
                {
                    if(app.session_player.id in app.session.world_state.choices)
                    {
                        app.choices = app.session.world_state.choices[app.session_player.id];
                    }
                }
            }

            //start tick tock
            app.run_tick_tock();
        },

        /**
         * after reconnection, load again
         */
        do_reload: function do_reload()
        {

        },

        /** send winsock request to get session info
        */
        send_get_session: function send_get_session(){
            app.send_message("get_session", {"player_key" : app.player_key});
        },
        
        /** take create new session
        *    @param message_data {json} session day in json format
        */
        take_get_session: function take_get_session(message_data){
            
            app.session = message_data.session;
            app.session_player = message_data.session_player;

            if(app.session.started)
            {
               
            }
            else
            {
               
            }            
            
            if(app.session.world_state.current_experiment_phase != 'Done')
            {
                                
            }

            if(app.session.world_state.current_experiment_phase == 'Instructions')
            {
                Vue.nextTick(() => {
                    app.process_instruction_page();
                    app.instruction_display_scroll();
                });
            }

            if(!app.first_load_done)
            {
                Vue.nextTick(() => {
                    app.do_first_load();
                });
            }
            else
            {
                Vue.nextTick(() => {
                    app.do_reload();
                });
            }
        },

        /** update start status
        *    @param message_data {json} session day in json format
        */
        take_update_start_experiment:function take_update_start_experiment(message_data){
            app.take_get_session(message_data);
        },

        /** update reset status
        *    @param message_data {json} session day in json format
        */
        take_reset_experiment: function take_reset_experiment(message_data){
            app.take_get_session(message_data);

            app.end_game_modal.hide();        
            
            app.help_modal.hide();

            app.notices_seen = [];
        },

        /**
        * update time and start status
        */
        take_update_time: function take_update_time(message_data){
          
            let status = message_data.value;

            if(status == "fail") return;

            let period_change = false;
            let period_earnings = 0;

            if (message_data.period_is_over)
            {
                period_earnings = message_data.earnings[app.session_player.id].period_earnings;
                app.session.world_state.session_players[app.session_player.id].earnings = message_data.earnings[app.session_player.id].total_earnings;
            }

            app.session.started = message_data.started;

            app.session.world_state.current_period = message_data.current_period;
            app.session.world_state.time_remaining = message_data.time_remaining;
            app.session.world_state.timer_running = message_data.timer_running;
            app.session.world_state.started = message_data.started;
            app.session.world_state.finished = message_data.finished;
            app.session.world_state.current_experiment_phase = message_data.current_experiment_phase;

            // app.session.world_state.finished = message_data.finished;
        
            //collect names
            if(app.session.world_state.current_experiment_phase == 'Names')
            {
                app.show_end_game_modal();
            }            

            //period has changed
            if(message_data.period_is_over)
            {
               
            }

        },

        /**
         * show the end game modal
         */
        show_end_game_modal: function show_end_game_modal(){
            if(app.end_game_modal_visible) return;
   
            app.help_modal.hide();

            app.end_game_modal.toggle();

            app.end_game_modal_visible = true;
            app.working = false;
        },

        /** take refresh screen
         * @param messageData {json} result of update, either sucess or fail with errors
        */
        take_refresh_screens: function take_refresh_screens(message_data){
            if(message_data.value == "success")
            {           
                app.session = message_data.session;
                app.session_player = message_data.session_player;
            } 
            else
            {
            
            }
        },

      
        /** take next period response
         * @param message_data {json}
        */
        take_update_next_phase: function take_update_next_phase(message_data){
            app.end_game_modal.hide();

            app.session.world_state.current_experiment_phase = message_data.current_experiment_phase;
            app.session.world_state.finished = message_data.finished;

            if(app.session.world_state.current_experiment_phase == 'Names')
            {
                app.show_end_game_modal();
            }
            else
            {
                app.hide_end_game_modal();
            }
            
            if(app.session.world_state.current_experiment_phase == 'Done' && 
                    app.session.parameter_set.survey_required && 
                    !app.session_player.survey_complete)
            {
                window.location.replace(app.session_player.survey_link);
            }

            if(app.session.world_state.current_experiment_phase == 'Run' || 
                app.session.world_state.current_experiment_phase == 'Instructions')
            {
                app.session.world_state = message_data.world_state;
                
                app.do_reload();
            }
        },

        /** hide choice grid modal modal
        */
        hide_end_game_modal: function hide_end_game_modal(){
            app.end_game_modal_visible=false;
        },

        //do nothing on when enter pressed for post
        onSubmit: function onSubmit(){
            //do nothing
        },
        
        {%include "subject/subject_home/summary/summary_card.js"%}
        {%include "subject/subject_home/test_mode/test_mode.js"%}
        {%include "subject/subject_home/instructions/instructions_card.js"%}
        {%include "subject/subject_home/help_doc_subject.js"%}
        {%include "subject/subject_home/choices/choices.js"%}
        {%include "subject/subject_home/helpers.js"%}
        {%include "subject/subject_home/results/results.js"%}
        {%include "subject/subject_home/chat_gpt/chat_gpt.js"%}


        /** clear form error messages
        */
        clear_main_form_errors: function clear_main_form_errors(){
            
            let s = app.form_ids;
            for(let i in s)
            {
                let e = document.getElementById("id_errors_" + s[i]);
                if(e) e.remove();
            }
        },

        /** display form error messages
        */
        display_errors: function display_errors(errors){
            for(let e in errors)
                {
                    //e = document.getElementById("id_" + e).getAttribute("class", "form-control is-invalid")
                    let str='<span id=id_errors_'+ e +' class="text-danger">';
                    
                    for(let i in errors[e])
                    {
                        str +=errors[e][i] + '<br>';
                    }

                    str+='</span>';

                    document.getElementById("div_id_" + e).insertAdjacentHTML('beforeend', str);
                    document.getElementById("div_id_" + e).scrollIntoView(); 
                }
        }, 

        /**
         * handle window resize event
         */
        handleResize: function handleResize(){
            
        },

    },

    mounted(){
        Vue.nextTick(() => {
            window.addEventListener('resize', app.handleResize);
        });
    },

}).mount('#app');

{%include "js/web_sockets.js"%}

  