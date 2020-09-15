var pollInterval = 5000;

function getData() {
    let jqxhr = $.getJSON('/api/get-data/', function(data) {
      updateLogList(data.log);
    }).done(function() {
        setTimeout(getData, pollInterval);
    }).fail(function() {
      console.log( "Failed to fetch data from server." );
    });
};


function updateLogList(log) {
    const logList = $('#log-list');
    let entryClass = 'list-group-item-info';
    if (logList.find('li').length < log.length) {
        logList.empty();
        for (const logEntry of log) {
            if (logEntry.level == 'ERROR') {
                entryClass = 'list-group-item-danger';
            } else if (logEntry.level == 'WARNING') {
                entryClass = 'list-group-item-warning';
            } else {
                entryClass = 'list-group-item-info';
            }
            logList.append('<li class="list-group-item '+entryClass+'">'+logEntry.msg+'</li>');
        }
    }
};


function startScraping(onFinished, onError) {
    let jqxhr = $.getJSON('/api/start-scraping', function(data) {
        console.log(data);
    }).done(onFinished()).fail(onError());
};


$(document).ready(function() {
    console.log('Ready!');
    getData();

    $('#get-latest-articles-btn').on('click', function(e) {
        let el = $(this);
        el.prop('disabled', true);
        $('#scraping-loading').slideDown('fast');
        startScraping(
            function() {
                el.prop('disabled', false);
                $('#scraping-loading').slideUp('fast');
            },
            function() {
                console.log( "Failed to fetch data from server." );
            }
        )
    });
});