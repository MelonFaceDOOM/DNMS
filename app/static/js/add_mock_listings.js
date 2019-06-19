$(document).on("click", ".submit", function(){
    var market_id = $(this).attr('market_id');
    var drugElements = $(".ms-selection .ms-selected");
    var drugs = []

    for (let i=0; i<drugElements.length; i++) {
        drugs.push(drugElements[i].textContent);
    }
    $.ajax({
        url : "/add_mock_listings",
        type : 'POST',
        data : {market_id: market_id, drugs: drugs},
        success: function(response) {
                $('#absent-drugs').html(response);
            }
    });
});