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
                     {"prompt": app.chat_text},
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


    