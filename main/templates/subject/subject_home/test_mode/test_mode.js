{%if session.parameter_set.test_mode%}

/**
 * return random number between min and max inclusive
 */
random_number: function random_number(min, max){
    //return a random number between min and max
    min = Math.ceil(min);
    max = Math.floor(max+1);
    return Math.floor(Math.random() * (max - min) + min);
},


do_test_mode: function do_test_mode(){

    if(worker) worker.terminate();

    {%if DEBUG%}
    console.log("Do Test Mode");
    {%endif%}

    if(app.end_game_modal_visible && app.test_mode)
    {
        if(app.session_player.name == "")
        {
            Vue.nextTick(() => {
                app.session_player.name = app.random_string(5, 20);
                app.session_player.student_id =  app.random_number(1000, 10000);

                app.send_name();
            })
        }

        return;
    }

    if(app.session.started &&
       app.test_mode
       )
    {
        
        switch (app.session.world_state.current_experiment_phase)
        {
            case "Instructions":
                app.do_test_mode_instructions();
                break;
            case "Run":
                app.do_test_mode_run();
                break;
            
        }        
       
    }

    // setTimeout(app.do_test_mode, app.random_number(1000 , 1500));
    worker = new Worker("/static/js/worker_test_mode.js");

    worker.onmessage = function (evt) {   
        app.do_test_mode();
    };

    worker.postMessage(0);
},

/**
 * test during instruction phase
 */
do_test_mode_instructions: function do_test_mode_instructions()
 {
    if(app.session_player.instructions_finished) return;
    if(app.working) return;
    
   
    if(app.session_player.current_instruction == app.session_player.current_instruction_complete)
    {

        if(app.session_player.current_instruction == app.instructions.instruction_pages.length)
            document.getElementById("instructions_start_id").click();
        else
            document.getElementById("instructions_next_id").click();

    }else
    {
        let session_player = app.session.world_state.session_players[app.session_player.id];
        let parameter_set = app.session.parameter_set;

        //take action if needed to complete page
        switch (app.session_player.current_instruction)
        {
            case app.instructions.action_page_1:
                if(parameter_set.experiment_mode == "Simultaneous")
                {   
                    app.do_test_mode_ranking(true);
                }
                else
                {
                    app.do_test_mode_sequential(true);
                }
                break;
            case app.instructions.action_page_2:
                app.do_test_mode_reviewing_results(true);
                break;
            case app.instructions.action_page_3:
                app.do_test_mode_chat(true);
                break;
        }   
    }

    
 },

/**
 * test during run phase
 */
do_test_mode_run: function do_test_mode_run()
{
    //do chat
    let go = true;
    
    if(app.session.world_state.finished) return;
        
    if(go)
    {
        let session_player = app.session.world_state.session_players[app.session_player.id];
        let parameter_set = app.session.parameter_set;
        if(session_player.status == "Chatting")
        {
            app.do_test_mode_chat(false);
        }
        else if(session_player.status == "Ranking")
        {
            if(parameter_set.experiment_mode == "Simultaneous")
            {
                app.do_test_mode_ranking(false);
            }
            else
            {
                app.do_test_mode_sequential(false);
            }
        }
        else if(session_player.status == "Reviewing_Results")
        {
            app.do_test_mode_reviewing_results(false);
        }
    }
},

/**
 * test during chat phase
 */
do_test_mode_chat: function do_test_mode_chat(do_imidiate = false)
{
    if (app.chat_working) return;

    if(app.random_number(1, 10) == 1 || do_imidiate )
    {
        //send chat message
        app.chat_text = "list 10 more cool facts";
        document.getElementById("send_chat_id").click();       
    }
    else if(app.random_number(1, 45) == 1)
    {
        //send done chatting
        app.send_done_chatting();
    }
    else if(app.random_number(1, 100) == 1)
    {
        //send clear chat gpt history
        app.send_clear_chat_gpt_history();
    }
},

/**
 * randomly rank the choices
 */
do_test_mode_ranking: function do_test_mode_ranking(do_imidiate = false)
{

    if(app.random_number(1, 30) != 1 && !do_imidiate)
    {
        return;
    }

    let group_size = app.session.parameter_set.group_size;
    let choices = [];

    //ranomly fill the choices array with numbers 1 to group_size
    for(let i=1;i<=group_size;i++)
    {
        choices.push(i);
    }
    //shuffle the choices array
    choices.sort(() => Math.random() - 0.5);

    app.choices = choices;

    let button = document.getElementById("submit_choices_button_id");
    if(button)
    {
        button.click();
    }
},

/**
 * test during ranking phase
 */
do_test_mode_sequential: function do_test_mode_sequential(do_imidiate = false)
{

    if(app.random_number(1, 10) != 1 && !do_imidiate)
    {
        return;
    }

    let choices = app.get_current_choices();

    for(let i=0;i<choices.length;i++)
    {
        if(!choices[i].owner)
        {
            app.choice = i;
            break
        }
    }

    let button = document.getElementById("submit_choices_button_id");
    if(button)
    {
        button.click();
    }
},

/**
 * test during reviewing results phase
 */
do_test_mode_reviewing_results: function do_test_mode_reviewing_results(do_imidiate = false)
{
    if(app.random_number(1, 30) != 1 && !do_imidiate)
    {
        return;
    }
    document.getElementById("ready_to_go_on_button_id").click();
},

{% endif %}