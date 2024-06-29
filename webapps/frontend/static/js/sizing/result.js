runId = null;
sizingGrids = [];
const saveColHeader = "Save to Components / Microgrids"
const urlParams = new URLSearchParams(window.location.search)
const query_string_all = urlParams.has('all');
const query_string_no_rounding = urlParams.has('precise');
const query_string_deficit = urlParams.get('deficit');

buildTab();

async function buildTab() {
  runId = $("#run-id").text();
  sizingGrids = await postData("sizing_results_get", null, {"id":runId, "display_all":query_string_all, "deficit_max":query_string_deficit});
  $(`#loading`).hide();
  sizingGrids = sizingGrids.data

  if (sizingGrids.length > 0) {
    const fixedColumns = ["ID", "Name", "Sizing Grid Deficit Ratio"]
    columnKeys = Object.keys(sizingGrids[0]);
    for (const x of fixedColumns) {
      var index = columnKeys.indexOf(x);
      if (index !== -1) {
        columnKeys.splice(index, 1);
      }
    }
    columnKeys = fixedColumns.concat(columnKeys).concat(saveColHeader)
  }

  if (sizingGrids.length > 0) {
    tabulate(sizingGrids, columnKeys, null, "#sizing-grids", !query_string_no_rounding);
    make_table_exportable("#sizing-grids", "sizing-grids-result-"+runId)
  }

  // insert links to save grids
  var index_id = $('#sizing-grids table th:contains(ID)').index();
  var index_save = $('#sizing-grids table th:contains('+saveColHeader+')').index();
  var table = document.getElementById("sizing-grids").getElementsByTagName('table')[0];
  if (typeof table !== "undefined") {
    for (var i = 1, row; row = table.rows[i]; i++) {
      var id = $('#sizing-grids table tr').eq(i).find('td').eq(index_id).text()
      var target = $('#sizing-grids table tr').eq(i).find('td').eq(index_save)
      target.html(
        '<a href="#" data-id="'+id+'" data-tabname="result" onclick="openConfirmSave(event)" class="card-link float-end">Save</a>'
      )
      target.addClass("sizing-grid-save")
    }
  }
}

function openConfirmSave(e) {
  e.preventDefault();
  const sizingGridId = e.target.dataset.id;
  const sizingGrid = sizingGrids.find(sizingGrid => sizingGrid.ID == sizingGridId);
  $('#confirm-save-result-modal .record-name').text(sizingGrid.Name);
  $('#save-result-btn').data('id', sizingGridId);
  $('#confirm-save-result-modal').modal('show');
}

async function saveToAccount(e) {
  const sizingGridId = $(e.target).data('id');
  const res = await postData("sizing_results_save_to_grids", null,  {"id": runId, "sizing_grid_id": sizingGridId});
  closeConfirmSaveModal(e);
  $('#confirm-save-result-modal').modal('hide');
  if (!res.error) {
    displayToastMessage('Sizing grid successfully saved to user-defined Components and Microgrids.');
  }
}
