// common variables
var timeout;
var timer;
var nanobar;
var status_url;
var status_div;

function check_existing_task(url) {
    // add task status elements
    div = $('<div class="progress"><div></div><div>0%</div><div>...</div><div>&nbsp;</div></div><hr>');
    $('#progress').append(div);
    status_div = div[0];
    status_url = url;
    // create a progress bar
    nanobar = new Nanobar({
        bg: '#44f',
        target: div[0].childNodes[0]
    });
    update_progress(status_url, nanobar, status_div);
};

$(document).on("click", "#start-bg-job", function start_task() {
    // send ajax POST request to start background job
    var scraper_name = "rechem";
    $.ajax({
        type: 'POST',
        url: '/scraping/starttask',
        data: {scraper_name: scraper_name},
        success: function(data, status, request) {
            status_url = request.getResponseHeader('Location');

            // remove start button from page
            $("#start-button").text("Scraping already running");
			// add task status elements
			div = $('<div class="progress"><div></div><div>0%</div><div>&nbsp;</div></div><hr>');
			$('#progress').append(div);
			status_div = div[0];
			// create a progress bar
			nanobar = new Nanobar({
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

        var status_msg = data['state'] + " - " + data['current'] + " / " + data['total']
        $("#status").text(status_msg);
        $('#next_url').text(data['next_url']);
        $('#successes').text(data['successes']);
        $('#failures').text(data['failures']);
        // if success or unexpected result
        if (data['state'] != 'PENDING' && data['state'] != 'PROGRESS' && data['state'] != "SUCCESS" && data['state'] != "NOT RUNNING") {
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
            if (data['sleeptime'] < 1) {
                timeleft=1
            }
            else {
                timeleft=data['sleeptime']
            }
            setTimeout(function() {
                update_progress(status_url, nanobar, status_div);
            }, timeleft * 1000);
        };
    });
};

$(document).on("click", "#kill-bg-job",function kill_task(task_id) {
    var scraper_name = "rechem";
    $.ajax({
        type: 'POST',
        url: '/scraping/kill_task',
        data: {scraper_name: scraper_name},
        success: function(data, status, request) {
            if (data['response'] == "task killed") {
                clearTimeout(timeout);
                clearInterval(timer);
                update_progress(status_url, nanobar, status_div)
                alert("task killed");
            }
            else if (data['response'] == "no task found") {
                alert("No task was running");
            }
            else {
                alert("Unexpected response from kill route")
            }
        },
        error: function() {
            alert('Unexpected error');
        }
    });
});
