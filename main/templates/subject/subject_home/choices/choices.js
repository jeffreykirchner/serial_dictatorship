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
submit_choices : function submit_choices() {
    
    app.choices_error_message = "";
    app.working = true;

    app.send_message("choices", 
                    {"choices": app.choices},
                     "group"); 
},

/***
 * handle the response from the server after submitting choices
 */
take_choices(message_data) {
    if (message_data.status === "success") {
        app.session.world_state.session_players[app.session_player.id].status = message_data.player_status;
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
},


    