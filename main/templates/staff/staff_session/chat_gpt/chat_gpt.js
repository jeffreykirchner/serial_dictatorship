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


    