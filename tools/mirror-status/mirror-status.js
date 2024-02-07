$(function() {
  $.tablesorter.addParser({
    id: 'hostname',
    is: function (s) {
      return false;
    },
    format: function (s, table, cell) {
      var $cell = $(cell);
      var t = $cell.attr('data-text') || s;
      var list_t = t.split('.');
      list_t.reverse();
      return list_t.join('.');
    },
    type: 'text'
  });

  // call the tablesorter plugin
  $("#results").tablesorter({
    theme: "bootstrap",
    widgets: [
      "columnSelector",
      "filter",
      "sort2Hash",
      "zebra",
    ],
    widgetOptions: {
      columnSelector_container: $('#columnSelector'),
      columnSelector_mediaquery: false,
      columnSelector_saveColumns: false,
      columnSelector_columns : {
        0 : "disable", /* disable; i.e. remove column from selector */
        1 : false,     /* start with column hidden */
        2 : true,      /* start with column visible; default for undefined columns */
      },
      filter_cssFilter: "form-control",
      filter_useParsedData: false,
    },
  });
});
