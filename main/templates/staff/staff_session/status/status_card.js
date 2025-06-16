get_status_table_values : function get_status_table_values() {
    let world_state = app.session.world_state;
    let parameter_set = app.session.parameter_set;
    let output = [];
    for(let i=world_state.current_period; i>0; i--) {
        for(let j in world_state.session_players_order) {
            let session_player_id = world_state.session_players_order[j];
            let session_player = world_state.session_players[session_player_id];
            let parameter_set_player = app.get_parameter_set_player_from_player_id(session_player_id);

            let v = {};
            v.period = i;
            v.group = parameter_set.parameter_set_groups[parameter_set_player.parameter_set_group].name;
            v.client_number = parameter_set_player.player_number;

            output.push(v);
        }
    }

    return output;
},