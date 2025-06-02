/**
 * return a json object of choices for the subject's current group and period
 *  */ 
take_results : function take_results(message_data) {
    app.working = false;
    app.session_player.period_results.push(message_data.period_results);
    app.session.world_state.session_players[app.session_player.id].status = "Reviewing_Results";
    app.session.world_state.session_players[app.session_player.id].earnings = message_data.earnings;
},


    