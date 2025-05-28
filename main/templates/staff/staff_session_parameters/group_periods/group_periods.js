/**show edit parameter set group
 */
show_edit_parameter_set_group_period: function show_edit_parameter_set_group(index){
    
    if(app.session.started) return;
    if(app.working) return;

    app.clear_main_form_errors();
    app.current_parameter_set_group_period = Object.assign({}, app.parameter_set.parameter_set_group_periods[index]);
    
    app.edit_parameterset_group_period_modal.toggle();
},

/** update parameterset group
*/
send_update_parameter_set_group_period: function send_update_parameter_set_group_period(){
    
    app.working = true;

    app.send_message("update_parameter_set_group_period", {"session_id" : app.session.id,
                                                           "parameterset_group_period_id" : app.current_parameter_set_group_period.id,
                                                           "form_data" : app.current_parameter_set_group_period});
},


/** add a new parameterset group
*/
send_auto_fill_parameter_set_group_periods: function send_auto_fill_parameter_set_group_periods(group_id){
    app.working = true;
    app.send_message("auto_fill_parameter_set_group_periods", {"session_id" : app.session.id});                                       
},