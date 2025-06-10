/**
 * return a json object of choices for the subject's current group and period
 *  */ 
get_current_choices : function get_current_choices() {
    let choice_list = [];

    // let choices = app.session.world_state.parameter_set.

    let parameter_set_player = app.get_parameter_set_player_from_player_id(app.session_player.id);

    let group = app.session.world_state.groups[parameter_set_player.parameter_set_group.toString()];

    return group.values[app.session.world_state.current_period.toString()];
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

    app.choices_error_message = "";
    app.working = true;

    app.send_message("choices_simultaneous", 
                    {"choices": app.choices},
                     "group"); 
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

    app.choices_error_message = "";
    app.working = true;

    app.send_message("choices_sequential", 
                    {"choice": app.choice},
                     "group");
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

    } else {
        app.working = false;
        app.choices_error_message = message_data.error_message;
    }
},

/**
 * send ready to go on to the server
 */
send_ready_to_go_on : function send_ready_to_go_on() {
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
    app.session.world_state.session_players[app.session_player.id].status = "Ranking";

    app.choices = [];
    app.choices_error_message = "";
    app.choice = null;

    // reset the active player group index for all groups
    for(let g in app.session.world_state.groups) {
        let group = app.session.world_state.groups[g];
        group.active_player_group_index = 0;
    }
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

    