/**
 * return data for status table
 */
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
            v.values = "";

            if(app.session.session_players[session_player_id].period_results.length>i-1)
            {
                let period_result = app.session.session_players[session_player_id].period_results[i-1];

                for(let k in period_result.values) {
     
                    v.values += parseFloat(period_result.values[k].value).toFixed(2);

                    if(parameter_set.experiment_mode == "Sequential")
                    {
                        if(period_result.values[k].owner == session_player_id)
                        {
                            v.values += ' (<i class=\'fas fa-check\'></i>)';
                        }
                    }
                    else if(parameter_set.experiment_mode == "Simultaneous")
                    {
                        v.values += ' (' + period_result.values[k].rank + ')';
                    }

                    v.values += ", ";
                }
                v.values = v.values.slice(0, -2);  // remove trailing comma and space

                v.priority_score = period_result.priority_score;
                v.order = period_result.order;
                v.prize = parseFloat(period_result.prize).toFixed(2);
                v.expected_order = period_result.expected_order;
                v.auto_submit = period_result.auto_submit;
            }

            output.push(v);
        }
    }

    return output;
},

