let newComponents = [];
let grids = [];
let quotas = [];
let components = [];
let componentTypes = [];
const pageType = $("meta[name='page-type']").attr("content"); 
const pageTitle = pageType === "microgrids" ? "Microgrid" : "Microgrid Sizing Template";

build();
addModalEvents();

async function build() {
  grids = await getData(pageType === "microgrids" ? "grids_get" : "sizing_grids_get");
  quotas = await getData("quota");
  components = await getData("components_get");
  componentTypes = await getData("component_types");
  buildList();
  $("#full-screen-loader").hide();
}

// Builds list of user's grid's components
function buildList() {
  const numGrids = grids.length;
  $("#title").text(`${numGrids} ${pageTitle}${numGrids > 1 ? "s" : ""}`);
  $('#list').empty();

  if (grids.length === 0) {
    $('#no-grids-message').show();
  }

  else {
    $('#no-grids-message').hide();

    // Map out grids using Bootstrap cards
    grids.forEach(grid => {
      $("#list").append(`
        <div class="widget">
          <h5>${grid.name}</h5>
            <div class="card-body">
              ${createGridCardComponentList(grid)}
              <div>
                <a href="${grid.id}" class="card-link float-start">View</a>
                <a href="#" id="${grid.id}-open-confirm-delete-btn" data-name="microgrids" class="card-link float-end delete">
                  Delete
                </a>
              </div>
          </div>
        </div>
      `);
      $(`#${grid.id}-open-confirm-delete-btn`).on('click', (e) => handleOpenConfirmDelete(e, grid));
    });
  }
}

function handleUserQuotaCheck(el, e) {
  const quota = pageType === "microgrids" ? quotas.grid : quotas.sizing;
  userQuotaCheck(grids.length, "grid", quota);
};

async function create(e) {
  e.preventDefault();
  let newGrid = {};
  newGrid['name'] = $('#new-modal #name').val();
  newGrid['description'] = $('#new-modal #description').val();
  newGrid['isSizingTemplate'] = pageType === "microgrids" ? 0 : 1;

  const res = await postData("grids_add", "#new-form", newGrid);

  if (!res.error) {
    $('#new-modal').modal('hide');
    displayToastMessage("New grid created!");
    build();
  }

}

// Opens the confirm delete modal and displays additional information
async function handleOpenConfirmDelete(e, grid) {
  openConfirmDeleteModal(e, grid, deleteGrid);
  const results = await getData("sizing_results_get");
  const gridResults = results.filter(r => r["Microgrid Sizing Template ID"] === grid.id);

  if (gridResults.length > 0) {
    createRelatedDataList(
      gridResults, 
      "The following microgrid sizing results will also be deleted:", 
      "Result ID"
    )
  }

  $('#confirm-delete-modal').modal('show');

}

async function deleteGrid(e) {
  const gridId = $(e.target).data('id');
  const res = await postData("grids_remove", null,  {id: gridId});

  if (!res.error) {
    closeConfirmDeleteModal(e);
    $('#confirm-delete-modal').modal('hide');
    displayToastMessage('Grid successfully deleted.');
    build();
  }

}