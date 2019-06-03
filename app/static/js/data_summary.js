$(document).on("click", ".rename_market", function(){

    var market_id = $(this).attr('market_id');
    var new_name = prompt("Please enter the new market name:", "");
    if (new_name == null || new_name == "") {
    }
    else {
        $.ajax({
            url : "/rename_market",
            type : 'POST',
            data : {market_id: market_id, new_name: new_name},
            success: function(response) {
                $('#market_name'+market_id).text(new_name)
            }
        });
    }
});

$(document).on("click", ".delete_market", function(){
    var market_id = $(this).attr('market_id');
    if (confirm('Are you sure you want to delete this market?')) {
        $.ajax({
            url : "/delete_market",
            type : 'POST',
            data : {market_id: market_id},
            success: function(response) {
                $('#data_summary').html(response);
            }
        });
    }
});

$(document).on("click", "#create_market", function(){
    var name = prompt("Please enter a name for the new market name:", "");
    if (name == null || name == "") {
        } else {
        $.ajax({
            url : "/create_market",
            type : 'POST',
            data : {name: name},
            success: function(response) {
                $('#data_summary').html(response);
            }
        });
    }
});