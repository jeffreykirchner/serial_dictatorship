get_current_parameter_set_group_period : function get_current_parameter_set_group_period() {
    let parameter_set = app.session.world_state.parameter_set;
    let current_period = app.session.world_state.current_period;
    
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