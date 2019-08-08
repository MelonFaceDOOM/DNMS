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
    // send ajax POST request to start background job
    var scraper_name = "test";
    $.ajax({
        type: 'POST',
        url: '/scraping/starttask',
        data: {scraper_name: scraper_name},
        success: function(data, status, request) {
            status_url = request.getResponseHeader('Location');

            // remove start button from page
            $("#start-button").text("Test is running");
            // add task status elements
            div = $('<div class="progress"><div></div><div>0%</div><div>&nbsp;</div></div><hr>');
            $('#progress').append(div);

            // create a progress bar
            var nanobar = new Nanobar({
                bg: '#44f',
                target: div[0].childNodes[0]
            });
            update_progress(status_url, nanobar, div[0]);

        },
        error: function(req, status, err) {
            alert(req.getResponseHeader('message-body'));
        }
    });
});

function update_progress(status_url, nanobar, status_div) {
    // send GET request to status URL
    $.getJSON(status_url, function(data) {
        //end function if no scraper found
        if (data['state'] == "Scraper not found") {
            alert(`No scraper associated with status_url: ${status_url}`);
            return;
        }
        percent = parseInt(data['current'] * 100 / data['total']);
        nanobar.go(percent);
        $(status_div.childNodes[1]).text(percent + '%');
        $(status_div.childNodes[2]).text(data['status']);

        $("#status").text(data['state']);
        $('#successes').text(data['successes']);
        $('#failures').text(data['failures']);
        // if success or unexpected result
        if (data['state'] != 'PENDING' && data['state'] != 'PROGRESS' && data['state'] != "SUCCESS"
            && data['state'] != "NOT RUNNING") {
            // something unexpected happened
            $("#status").text(`Unexpected error. Task state is: ${data['state']}`);
        }
        else if (data['state'] == "SUCCESS" || data['state'] == "NOT RUNNING") {
            // the program either hasn't started or is finished
            // I think the state immediately changes from success to not running as soon as the task
            // completes, which is why checking for just success is unreliable
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
                if(timeleft <= 0){
                    clearInterval(timer);
                    $('#countdowntimer').text("0");
                }
                timeleft -= 1;
            }, 1000);
            // wait until sleeptime is complete
            setTimeout(function() {
                update_progress(status_url, nanobar, status_div);
            }, data['sleeptime'] * 1000);
        };
    });
};

$(document).on("click", "#kill-bg-job",function kill_task(task_id) {
    var scraper_name = "test";
    $.ajax({
        type: 'POST',
        url: '/scraping/kill_task',
        data: {scraper_name: scraper_name},
        success: function(data, status, request) {
            alert("task killed");
        },
        error: function() {
            alert('Unexpected error');
        }
    });
});