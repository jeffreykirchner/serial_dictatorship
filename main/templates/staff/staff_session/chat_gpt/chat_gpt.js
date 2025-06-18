/**
 * take chat gpt response
 */
take_process_chat_gpt_prompt : function take_chat_gpt_response(message_data) {
    app.chat_history.unshift(message_data);

    if(app.chat_history.length > 20) {
        app.chat_history.pop();
    }
},


    