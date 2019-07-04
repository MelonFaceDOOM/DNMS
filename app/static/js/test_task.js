function check_existing_task(status_url) {
    // add task status elements
    div = $('<div class="progress"><div></div><div>0%</div><div>...</div><div>&nbsp;</div></div><hr>');
    $('#progress').append(div);
    // create a progress bar
    var nanobar = new Nanobar({
        bg: '#44f',
        target: div[0].childNodes[0]
    });
    update_progress(status_url, nanobar, div[0]);
};

$(document).on("click", "#start-bg-job", function start_task() {
    // add task status elements
    div = $('<div class="progress"><div></div><div>0%</div><div>...</div><div>&nbsp;</div></div><hr>');
    $('#progress').append(div);
    // create a progress bar
    var nanobar = new Nanobar({
        bg: '#44f',
        target: div[0].childNodes[0]
    });
    // send ajax POST request to start background job
    var scraper_name = "test";
    $.ajax({
        type: 'POST',
        url: '/scraping/starttesttask',
        data: {scraper_name: scraper_name },
        success: function(data, status, request) {
            if (data == {}) {
                alert('No Scraper by name $(scraper_name) found');
            } else {
                status_url = request.getResponseHeader('Location');
                update_progress(status_url, nanobar, div[0]);
            }
        }
        error: function() {
            alert('Unexpected error');
        }
    });
});

function update_progress(status_url, nanobar, status_div) {
    // send GET request to status URL
    $.getJSON(status_url, function(data) {
        //end function if null response
        if (data=={}) {
            alert("Null response for $(status_url)");
            return;
        }
        percent = parseInt(data['current'] * 100 / data['total']);
        nanobar.go(percent);
        $(status_div.childNodes[1]).text(percent + '%');
        $(status_div.childNodes[2]).text(data['status']);
        $('#successes').text('Successes: ' + data['successes']);
        $('#failures').text('Failures: ' + data['failures']);

        // check if status is pending or progress
        if (data['state'] != 'PENDING' && data['state'] != 'PROGRESS') {
            if ('result' in data) {
                // show result
                $(status_div.childNodes[3]).text('Result: ' + data['result']);
            }
            else {
                // something unexpected happened
                $(status_div.childNodes[3]).text('Result: ' + data['state']);
            }
        }
        else if (data['state'] == "PENDING") {
            // rerun in 1 seconds
            setTimeout(function() {
                update_progress(status_url, nanobar, status_div);
            }, 1000);
        }
        //start countdown timer and wait that amount of time
        else if (data['state'] == "PROGRESS") {
            var timeleft = data['sleeptime'];
            var timer = setInterval(function(){
                $('#countdowntimer').text(timeleft);
                timeleft -= 1;
                if(timeleft <= 0){
                    clearInterval(timer);
                    $('#countdowntimer').text("Finished");
                }
            }, 1000);
            // wait until sleeptime is complete
            setTimeout(function() {
                update_progress(status_url, nanobar, status_div);
            }, data['sleeptime'] * 1000);
        };
    });
};

$(document).on("click", "#kill-bg-job",function kill_task(task_id) {
    $.ajax({
        type: 'POST',
        url: '/scraping/kill_task/'+task_id,
        success: function() {
            alert("task killed")
        },
        error: function() {
            alert('Unexpected error');
        }
    });
});