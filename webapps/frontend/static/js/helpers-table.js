function formatDataListAsDict (dataArr, columnKeys, maxRows) {
  let dictList = [];
  if (maxRows && maxRows < dataArr.length) {
    dataArr = dataArr.slice(0, maxRows);
  }
  dataArr.forEach(row => {
    const dict = {};
    row.forEach((value, i) => {
      dict[columnKeys[i]] = value;
    });
    dictList.push(dict);
  });
  return dictList;
}

function isFloat(n){
  return Number(n) === n && n % 1 !== 0;
}

function formatValue(value) {
  if (isFloat(value)) {
    var log10 = value ? Math.floor(Math.log10(value)) : 0,
    div = log10 < 0 ? Math.pow(10, 1 - log10) : 100;
    value = Math.round(value * div) / div;
  }
  return value
}

// The table generation function
function tabulate(data, columnKeys, columnLabels, tableParentElId, roundDecimals=true) {

  if (data.length > 0 && !columnKeys) {
    columnKeys = Object.keys(data[0]);
  }

  if (!columnLabels) {
    columnLabels = columnKeys;
  }

  table = d3.select(tableParentElId).append("table")
    .attr('class','table table-bordered table-hover')
    .attr("style", "margin-left: 0px")

  table.append("thead");
  table.append("tbody");

  // append the header row
  table.select('thead').append("tr")
    .selectAll("th")
    .data(columnLabels)
    .enter()
    .append("th");

  table.select('thead')
    .select('tr')
    .selectAll('th')
    .data(columnLabels)
    .text(label => label)

  // create a row for each object in the data
  var rows = table.select('tbody').selectAll("tr").data(data).join(
    (enter) => enter.append("tr").classed("even", (d, i) => i % 2 == 1),
    (update) => update,
    (exit) => exit.remove()
  );

  rows.selectAll("td")
    .data((row) => {
      return columnKeys.map((column) => {
      return {column: column, value: row[column]};
      });
    }).join(
      (enter) => {
        enter.append("td")
          .attr("style", "font-family: Courier")
          .classed('right', (d, i) => {
            return i % 2 == 1;
          })
          .html(function(d, i) {
            return roundDecimals ? formatValue(d.value) : d.value
          })
      },
      (update) => {
        update.html(function(d, i) {                            
          return roundDecimals ? formatValue(d.value) : d.value
        })
      },
      (exit) => exit.remove()
    )
}

function make_table_exportable(tableParentElId, filename) {
    var $table = $(tableParentElId).select('table')
    var $button = $("<button type='button'>");
    $button.text("download table");
    $button.insertBefore($table);
    $button.click({"parentElId":tableParentElId, "filename":filename}, export_table);
}

function saveAs(uri, filename) {
  var link = document.createElement('a');
  if (typeof link.download === 'string') {
    link.href = uri;
    link.download = filename;
    document.body.appendChild(link); //Firefox requires the link to be in the body
    link.click();
    document.body.removeChild(link);
  } else {
    window.open(uri);
  }
}

function export_table(event) {
  var table = $(event.data.parentElId).find('table')
  var csv = table.table2csv('return');
  var file = 'data:text/csv;filename=da.txt;charset=UTF-8,'+encodeURIComponent(csv);
  saveAs(file, event.data.filename);
}
