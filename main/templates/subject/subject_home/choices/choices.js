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
    //all choices must be ranked
    let current_choices = app.get_current_choices();
    if (app.choices.length < current_choices.length) {
        app.choices_error_message = "You must rank all choices.";
        return;
    }

    //choices must be an integer greater than 0 and less than or equal to the number of get_current_choices().length
    //each choice must be unique
    let choice_set = new Set(app.choices);
    if (choice_set.size !== app.choices.length) {
        app.choices_error_message = "You must rank each choice uniquely.";
        return;
    }
    for (let i = 0; i < app.choices.length; i++) {
        if (app.choices[i] < 1 || app.choices[i] > current_choices.length) {
            app.choices_error_message = "You must rank each choice between 1 and " + current_choices.length + ".";
            return;
        }
    }
    app.choices_error_message = "";
    app.session.world_state.session_players[app.session_player.id].status = "Finished_Ranking";

    app.send_message("choices", 
                    {"choices": app.choices},
                     "group"); 
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
take_start_next_period : function take_start_next_period() {
    app.session.world_state.session_players[app.session_player.id].status = "Ranking";
   
},


    