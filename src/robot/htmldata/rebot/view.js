function removeJavaScriptDisabledWarning() {
    // Not using jQuery here for maximum speed
    document.getElementById('javascript_disabled').style.display = 'none';
}

function addJavaScriptDisabledWarning() {
    document.getElementById('javascript_disabled').style.display = 'block';
}

function initLayout(suiteName, type) {
    parseTemplates();
    setTitle(suiteName, type);
    addHeader();
    addReportOrLogLink(type);
}

function parseTemplates() {
    $('script[type="text/x-jquery-tmpl"]').map(function (idx, elem) {
        $.template(elem.id, elem.text);
    });
}

function setTitle(suiteName, type) {
    var givenTitle = window.settings.title;
    var title = givenTitle ? givenTitle : suiteName + " Test " + type;
    document.title = util.unescape(title);
}

function addHeader() {
    createGenerated(window.output.generatedTimestamp,
                    window.testdata.generated().getTime()
    ).appendTo($('#header'));
    $.tmpl('' +
        '<div id="top_right_header"><div id="report_or_log_link">' +
        '<a href="#"></a>' +
        '</div></div>' +
        '<h1>${title}</h1>', {
        title: document.title
    }).appendTo($('#header'));
}

function createGenerated(generated, generatedMillis) {
    return $.tmpl('<div id="generated">' +
    '<span>Generated<br>${generated}</span><br>' +
    '<span id="generated_ago">${generatedAgo} ago</span>' +
    '</div>', {
        generated: generated,
        generatedAgo: util.createGeneratedAgoString(generatedMillis)
    });
}

function addReportOrLogLink(myType) {
    var url;
    var text;
    if (myType == 'Report') {
        url = window.settings.logURL;
        text = 'LOG';
    } else {
        url = window.settings.reportURL;
        text = 'REPORT';
    }
    if (url) {
        $('#report_or_log_link a').attr('href', url);
        $('#report_or_log_link a').text(text);
    } else {
        $('#report_or_log_link').remove();
    }
}

function addStatistics() {
    var statHeaders =
        '<th class="col_stat">Total</th>' +
        '<th class="col_stat">Pass</th>' +
        '<th class="col_stat">Fail</th>' +
        '<th class="col_elapsed">Elapsed</th>' +
        '<th class="col_graph">Pass / Fail</th>';
    var statTable =
        '<h2>Test Statistics</h2>' +
        '<table class="statistics" id="total_stats"><thead><tr>' +
        '<th class="col_stat_name">Total Statistics</th>' + statHeaders +
        '</tr></thead><tbody></tbody></table>' +
        '<table class="statistics" id="tag_stats"><thead><tr>' +
        '<th class="col_stat_name">Statistics by Tag</th>' + statHeaders +
        '</tr></thead><tbody></tbody></table>' +
        '<table class="statistics" id="suite_stats"><thead><tr>' +
        '<th class="col_stat_name">Statistics by Suite</th>' + statHeaders +
        '</tr></thead><tbody></tbody></table>';
    $(statTable).appendTo('#statistics_container');
    $.map(['total', 'tag', 'suite'], addStatTable);
    addTooltipsToElapsedTimes();
    enableStatisticsSorter();
}

function addTooltipsToElapsedTimes() {
    $('#total_stats .col_elapsed, #tag_stats .col_elapsed').attr('title',
        'Total execution time of these test cases. ' +
        'Excludes suite setups and teardowns.');
    $('#suite_stats .col_elapsed').attr('title',
        'Total execution time of this test suite.');
}

function enableStatisticsSorter() {
    $(".statistics").tablesorter({headers: {5: {sorter: false}}});
}

function addStatTable(tableName) {
    var stats = window.testdata.statistics()[tableName];
    if (tableName == 'tag' && stats.length == 0) {
        renderNoTagStatTable();
    } else {
        var templateName = tableName + 'StatisticsRowTemplate';
        renderStatTable(tableName, templateName, stats);
    }
}

function renderNoTagStatTable() {
    $.tmpl('no_tags_row').appendTo($('#tag_stats'));
}

function renderStatTable(tableName, templateName, stats) {
    var tableId = "#" + tableName + "_stats";
    // Need explicit for loop because $.tmpl() does not handle very large lists
    for (var i = 0; stats !== undefined && i < stats.length; i++) {
        $.tmpl(templateName , stats[i]).appendTo($(tableId + '> tbody'));
    }
}

$.template("stat_columns",
    '<td class="col_stat">${total}</td>' +
    '<td class="col_stat">${pass}</td>' +
    '<td class="col_stat">${fail}</td>' +
    '<td class="col_elapsed">${elapsed}</td>' +
    '<td class="col_graph">' +
      '{{if total}}' +
      '<div class="graph">' +
        '<div class="pass_bar" style="width: ${passWidth}%;" title="${passPercent}%"></div>' +
        '<div class="fail_bar" style="width: ${failWidth}%;" title="${failPercent}%"></div>' +
      '</div>' +
      '{{else}}' +
      '<div class="empty_graph"></div>' +
      '{{/if}}' +
    '</td>'
);

$.template('no_tags_row',
    '<tr>' +
    '<td class="col_stat_name">No Tags</td>' +
    '<td class="col_stat"></td>' +
    '<td class="col_stat"></td>' +
    '<td class="col_stat"></td>' +
    '<td class="col_elapsed">0.000</td>' +
    '<td class="col_graph">' +
      '<div class="empty_graph"></div>' +
    '</td>' +
    '</tr>'
);

$.template('suiteStatusMessageTemplate',
    '${critical} critical test, ' +
    '${criticalPassed} passed, ' +
    '<span class="{{if criticalFailed}}fail{{else}}pass{{/if}}">${criticalFailed} failed</span><br>' +
    '${total} test total, ' +
    '${totalPassed} passed, ' +
    '<span class="{{if totalFailed}}fail{{else}}pass{{/if}}">${totalFailed} failed</span>'
);
