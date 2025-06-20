/**
 * send chat gpt prompt to server
 *  */ 
send_process_chat_gpt_prompt : function send_process_chat_gpt_prompt(message_data) {

    app.working = true;

    let prompt = {"role":"user", "content": app.chat_text};

    app.chat_history.unshift(prompt);

    //set to font awesome spinner
    app.chat_button_text = '<i class="fas fa-spinner fa-spin"></i>';   

    app.send_message("process_chat_gpt_prompt", 
                     {"prompt": app.chat_text,
                      "current_period": app.session.world_state.current_period, 
                     },
                      "self");

    app.chat_text = "";
},

/**
 * take chat gpt response
 */
take_process_chat_gpt_prompt : function take_chat_gpt_response(message_data) {
    app.working = false;
    app.chat_button_text = 'Chat <i class="far fa-comments"></i>';

    if (message_data.status == "success") {       
        app.chat_history.unshift(message_data.response);        
    } else {
        
    }
},

/**
 * clear chat gpt history
 */
send_clear_chat_gpt_history: function send_clear_chat_gpt_history() {
    if(app.working) {
        return;
    }

    app.clear_chat_gpt_history_modal.hide();
    app.working = true;
    app.send_message("clear_chat_gpt_history", 
                     {},
                      "self");
},

/**
 * take clear chat gpt history
 */
take_clear_chat_gpt_history: function take_clear_chat_gpt_history(message_data) {
    app.working = false;
    
    if (message_data.status == "success") {
        app.chat_history = message_data.chat_history;
    } else {
       
    }
},

/**
 * scroll to this element in chat gpt history
 */
scroll_chat_gpt_history_to_bottom: function scroll_chat_gpt_history_to_bottom(id) {
    Vue.nextTick(() => {
        // if (app.last_scroll_chat_gpt_history_to_bottom == id) {
        //     return;
        // }
        app.last_scroll_chat_gpt_history_to_bottom = id;        
        document.getElementById(id).scrollIntoView();
    });
},


    