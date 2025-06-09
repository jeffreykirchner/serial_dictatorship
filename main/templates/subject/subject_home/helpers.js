get_current_parameter_set_group_period : function get_current_parameter_set_group_period() {
    let parameter_set = app.session.world_state.parameter_set;
    let current_period = app.session.world_state.current_period;
    let parameter_set_group_id = parameter_set.parameter_set_group_periods_order[current_period-1];

    return app.session.world_state.parameter_set_groups[parameter_set_group_id];  
},

/**
 * get the parameter set player from the player id
*/
get_parameter_set_player_from_player_id: function get_parameter_set_player_from_player_id(player_id)
{
    try 
    {
        let parameter_set_player_id = app.session.world_state.session_players[player_id].parameter_set_player_id;
        return app.session.parameter_set.parameter_set_players[parameter_set_player_id];
    }
    catch (error) {
        return {id_label:null};
    }
},

/**
 * get earnings display
 */
get_earnings_display: function get_earnings_display(earnings)
{
    // $[[(Math.ceil(Number(session.world_state.session_players[p].earnings))/100).toFixed(2)]]

    let v = parseFloat(earnings);
    
    if(earnings < 0)
    {
        return "-$" + v.toFixed(2);
    }
    else
    {
        return "$" + v.toFixed(2);
    }
},