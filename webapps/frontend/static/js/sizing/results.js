const idColHeader = "Result ID"
const gridColHeader = "Microgrid Sizing Template"
const powerloadColHeader = "Powerload"
const simulationStartHeader = "Simulation Start"
const deleteColHeader = "Delete"

results = [];

buildTab();

async function buildTab() {
  results = await getData("sizing_results_get");
  $("#results").html("")
  if (results.length > 0) {
    const columnKeys = [idColHeader, gridColHeader, powerloadColHeader, 
                        simulationStartHeader, deleteColHeader]
    tabulate(results, columnKeys, null, "#results", false);

    // insert links to view and delete results
    var index_id = $('#results table th:contains('+idColHeader+')').index();
    var index_delete = $('#results table th:contains('+deleteColHeader+')').index();
    var table = document.getElementById("results").getElementsByTagName('table')[0];
    for (var i = 1, row; row = table.rows[i]; i++) {
      var id = $('#results table tr').eq(i).find('td').eq(index_id).text()
      // insert link to view
      var target = $('#results table tr').eq(i).find('td').eq(index_id)
      target.html(
        '<a href="'+id+'">'+id+'</a>'
      )
      // insert link to delete
      var target = $('#results table tr').eq(i).find('td').eq(index_delete)
      target.html(
        '<a href="#" data-id="'+id+'" data-tabname="result" onclick="openConfirmDelete(event)" class="card-link float-end">Delete</a>'
      )
      target.addClass("sizing-grid-save")
    }
  }
}

function openConfirmDelete(e) {
  e.preventDefault();
  const runId = e.target.dataset.id;
  const run = results.find(result => result[idColHeader] == runId);
  $('#confirm-delete-result-modal .record-name').text(runId);
  $('#delete-result-btn').data('id', runId);
  $('#confirm-delete-result-modal').modal('show');
}

async function deleteRun(e) {
  const runId = $(e.target).data('id');
  const res = await postData("sizing_results_remove", null,  {"id": runId});
  closeConfirmDeleteModal(e);
  $('#confirm-delete-result-modal').modal('hide');
  if (!res.error) {
    displayToastMessage('Sizing run successfully deleted.');
  }
  buildTab()
}
