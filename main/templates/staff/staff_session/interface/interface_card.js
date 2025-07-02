take_start_next_period: function take_start_next_period(message_data) {
    let world_state = app.session.world_state;
    let session_players = world_state.session_players;

    world_state.current_period = message_data.current_period;

    for(let i in session_players) {
        session_players[i].status = message_data.session_players[i].status;
    }
},

/**
 * take the result of the period
 */
take_result : function take_result(message_data){

    let period_results = message_data.period_results;
    let session_players = message_data.session_players;

    // add period results to session players
    for(let i in period_results) {
        let period_result = period_results[i];
        // process each period_result as needed
        app.session.session_players[i].period_results.push(period_result);
    }

    //update session player's status and earnings
    for(let i in session_players) {
        let session_player = session_players[i];
        let session_player_local = app.session.world_state.session_players[i];

        if(session_player) {
           session_player_local.status = session_player.status;
            session_player_local.earnings = session_player.earnings;
        }
    }
},

/**
 * return the plain version of player status
 */
convert_player_status: function convert_player_status(status_text) {
    switch(status_text) {
        case "Ranking":
            return "Ranking";
        case "Reviewing_Results":
            return "Reviewing Results";
        case "Finished_Ranking":
            return "Finished Ranking";       
        case "Waiting":
            return "Waiting";
        case "Chatting":
            return "Chatting";
        case "Finished_Chatting":
            return "Finished Chatting";
        default:
            return "---";
    }
},

/**
 * take ready to go on status
 */
take_update_status: function take_update_status(message_data) {
    let session_player = app.session.world_state.session_players[message_data.player_id];

    if(session_player) {
        session_player.status = message_data.player_status;
    }
},

/**
 * take update choices sequential
 * @param message_data {json} message data containing player_id and status
 */
take_update_choices_sequential: function take_update_choices_sequential(message_data) {
    let session_player = app.session.world_state.session_players[message_data.player_id];

    if(session_player) {
        session_player.status = message_data.player_status;
    }
},

/**
 * take done chatting
 */
take_done_chatting: function take_done_chatting(message_data) {
    app.chat_working = false;
    
    let subject_status = message_data.subject_status;

    for (let i in subject_status) {
        app.session.world_state.session_players[i].status = subject_status[i];
    }
},