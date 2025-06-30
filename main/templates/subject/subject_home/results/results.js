/**
 * return a json object of choices for the subject's current group and period
 *  */ 
take_results : function take_results(message_data) {
    let parameter_set_player = app.get_parameter_set_player_from_player_id(app.session_player.id);
    let current_period = app.session.world_state.current_period;

    app.working = false;
    app.session_player.period_results.push(message_data.period_results);
    app.session.world_state.session_players[app.session_player.id].status = "Reviewing_Results";
    app.session.world_state.session_players[app.session_player.id].earnings = message_data.earnings;

    app.session.world_state.groups[parameter_set_player.parameter_set_group].values[current_period] = message_data.period_results.values;

    app.setup_timer();
},


    