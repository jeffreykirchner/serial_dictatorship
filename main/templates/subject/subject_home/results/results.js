/**
 * return a json object of choices for the subject's current group and period
 *  */ 
take_results : function take_results(message_data) {

    app.session_player.period_results[app.session.world_state.current_period] = message_data.period_results;
},


    