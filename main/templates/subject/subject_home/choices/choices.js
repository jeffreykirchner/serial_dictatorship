/**
 * return a json object of choices for the subject's current group and period
 *  */ 
get_current_choices : function get_current_choices() {
    // let choice_list = [];

    // let choices = app.session.world_state.parameter_set.

    if(app.session.world_state.current_experiment_phase == 'Instructions') 
    {
        let choices = app.instructions.example_values.split(",");
        let result = [];
        //conver to float
        for(let i=0; i < choices.length; i++) {
            result.push({value: choices[i], owner: null});
        }

        result[1].owner = -1;

        return result;
    }
    else
    {
        let parameter_set_player = app.get_parameter_set_player_from_player_id(app.session_player.id);

        let group = app.session.world_state.groups[parameter_set_player.parameter_set_group.toString()];

        return group.values[app.session.world_state.current_period.toString()];
    }
},

/**
 * return the current priority score
 */
get_current_priority_score : function get_current_priority_score() {
    let parameter_set_player = app.get_parameter_set_player_from_player_id(app.session_player.id);
    let group = app.session.world_state.groups[parameter_set_player.parameter_set_group.toString()];

    return group.session_players[app.session_player.id][app.session.world_state.current_period.toString()].priority_score;
},

/**
validate and submit subject choices to the server
 */
submit_choices_simultaneous : function submit_choices() {

    if(app.session.world_state.current_experiment_phase == 'Instructions') 
    {

    }
    else
    {
        if(app.working) return; // don't submit if already working
        app.timer_running = false; // stop the timer

        app.choices_error_message = "";
        app.working = true;

        app.send_message("choices_simultaneous", 
                        {"choices": app.choices},
                        "group"); 
    }
},

/***
 * handle the response from the server after submitting choices
 */
take_choices_simultaneous(message_data) {
    if (message_data.status === "success") {
        app.session.world_state.session_players[app.session_player.id].status = message_data.player_status;
    } else {
        app.working = false;
        app.choices_error_message = message_data.error_message;
    }
},

/**
 * submit choices sequentially
 */
submit_choices_sequential : function submit_choices_sequential() {

    if(app.session.world_state.current_experiment_phase == 'Instructions') 
    {

    }
    else
    {
        if(app.working) return; // don't submit if already working
        app.timer_running = false; // stop the timer

        app.choices_error_message = "";
        app.working = true;
        app.send_message("choices_sequential", 
                        {"choice": app.choice},
                        "group");
    }
},

/**
 * handle the response from the server after submitting choices sequentially
 */
take_choices_sequential(message_data) {
    if (message_data.status === "success") {
        let parameter_set_player = app.get_parameter_set_player_from_player_id(app.session_player.id);
        let current_period = app.session.world_state.current_period;
        let player_id = message_data.player_id;

        app.session.world_state.groups[parameter_set_player.parameter_set_group].active_player_group_index = message_data.active_player_group_index;
        app.session.world_state.groups[parameter_set_player.parameter_set_group].values[current_period] = message_data.values;
        app.session.world_state.session_players[player_id].status = message_data.player_status;

        app.working = false;
        
        app.setup_timer();
    } else {
        app.working = false;
        app.choices_error_message = message_data.error_message;
    }
},

/**
 * send ready to go on to the server
 */
send_ready_to_go_on : function send_ready_to_go_on() {
    if(app.working) return; // don't send if already working
    app.timer_running = false; // stop the timer

    app.session.world_state.session_players[app.session_player.id].status = "Waiting";
    app.send_message("ready_to_go_on", 
                    {},
                     "group"); 
},

/**
 * start the next period
 */
take_start_next_period : function take_start_next_period(message_data) {

    app.session.world_state.current_period = message_data.current_period;
   
    let subject_status = message_data.subject_status;

    for (let i in subject_status) {
        app.session.world_state.session_players[i].status = subject_status[i];
    }

    app.choices = [];
    app.choices_error_message = "";
    app.choice = null;

    // reset the active player group index for all groups
    for(let g in app.session.world_state.groups) {
        let group = app.session.world_state.groups[g];
        group.active_player_group_index = 0;
    }

    app.setup_timer();
},

/**
 * get active player id
 */
get_active_player_id : function get_active_player_id() {
    let parameter_set_player = app.get_parameter_set_player_from_player_id(app.session_player.id);
    let group = app.session.world_state.groups[parameter_set_player.parameter_set_group.toString()];
    let current_period = app.session.world_state.current_period;

    return group.player_order[current_period][group.active_player_group_index];
},

/**
 * show submit choices button
 */
show_submit_choices_button : function show_submit_choices_button() {

    if(app.session.world_state.session_players[app.session_player.id].status != 'Ranking') return false;

    if(app.session.parameter_set.experiment_mode == 'Sequential') {
        if(app.get_active_player_id() != app.session_player.id) {
            return false; // not the active player
        }
    }

    return true
},

/**
 * timer setup
 */
setup_timer : function setup_timer() {

    if(app.session.world_state.session_players[app.session_player.id].status == 'Reviewing_Results') {
        // if the player is reviewing results, do not start the timer
        app.time_remaining = app.session.parameter_set.ready_to_go_on_length;        
        app.timer_last_pulse = Date.now();
        app.timer_running = true;
    }
    if(app.session.world_state.session_players[app.session_player.id].status == 'Chatting') {
        // if the player is finished ranking, do not start the timer
        app.time_remaining = app.session.parameter_set.chat_gpt_length;
        app.timer_last_pulse = Date.now();
        app.timer_running = true;
    }
    else if(app.session.parameter_set.experiment_mode == 'Sequential') {
        // start submission timer for the active player
        if(app.show_submit_choices_button()) {
            app.time_remaining = app.session.parameter_set.period_length;            
            app.timer_last_pulse = Date.now();
            app.timer_running = true;
        }
    }
    else if(app.session.parameter_set.experiment_mode == 'Simultaneous') {
        // start submission timer for all players
        if(app.show_submit_choices_button()) {
            app.time_remaining = app.session.parameter_set.period_length;           
            app.timer_last_pulse = Date.now();
            app.timer_running = true;
        }
    }
},

/**
 * timer expired, do action
 */
timer_expired : function timer_expired() {

    try {

        if(app.session.world_state.session_players[app.session_player.id].status == 'Reviewing_Results') {
            app.send_ready_to_go_on();
        }
        else if(app.session.world_state.session_players[app.session_player.id].status == 'Chatting') {
            app.send_done_chatting();
        }
        else
        {
            if(app.session.parameter_set.experiment_mode == 'Sequential') {
                // if the active player did not submit choices, submit choices with empty array
                if(app.show_submit_choices_button()) {
                    
                    let choices = app.get_current_choices();

                    for(let i=0; i < choices.length; i++) {
                        let choice = choices[i];
                        if(!choice.owner) {
                            app.choice = i;
                        }
                    }

                    app.submit_choices_sequential();
                }
            }
            else if(app.session.parameter_set.experiment_mode == 'Simultaneous') {
                //if player does not submit, sumbit choices from 1 to n

                app.choices = [];

                for(let i=0; i < app.session.parameter_set.group_size; i++) {
                    app.choices.push(i+1);
                }

                app.submit_choices_simultaneous();
            }
        }
    }
    catch (error) {
        console.error("Error in timer_expired: ", error);        
    }
},

    