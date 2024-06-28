let newComponents = [];
let grids = [];
let quotas = [];
let components = [];
let componentTypes = [];
const pageType = $("meta[name='page-type']").attr("content"); 
const pageTitle = pageType === "microgrids" ? "Microgrid" : "Microgrid Sizing Template";

// Add modal event listeners
$(`#new-grid-modal`).on('hidden.bs.modal', clearNewGridFields);

buildTab();

async function buildTab() {
  grids = await getData(pageType === "microgrids" ? "grids_get" : "sizing_grids_get");
  quotas = await getData("quota");
  components = await getData("components_get");
  componentTypes = await getData("component_types");
  buildList();
}

// Builds list of user's grid's components
function buildList() {
  const numGrids = grids.length;
  $("#grids-title").text(`${numGrids} ${pageTitle}${numGrids > 1 ? "s" : ""}`);
  $('#grid-main-view #grids-list').empty();
  $('#grid-main-view').show();
  $('#grid-edit-view').hide();

  if (grids.length === 0) {
    $('#no-grids-message').show();
  }

  else {
    $('#no-grids-message').hide();

    // Map out grids using Bootstrap cards
    grids.forEach(grid => {
      $("#grids-list").append(`
        <div class="col">
          <div class="card grid-card" style="width: 18rem;">
            <div class="card-body">
              <h5 class="card-title">${grid.name}</h5>
              <span class="text-secondary">${grid.components.length} components</span>
              <div class="card-text description">${grid.description}</div>
              <a href="${grid.id}" id="grid-${grid.id}-edit-btn" data-id="${grid.id}" class="card-link float-start" onclick="setCurrentGrid(event)">View</a>
              <a href="#" id="grid-${grid.id}-open-confirm-delete-btn" data-id="${grid.id}" data-tabname="microgrids" onclick="openConfirmDelete(event)" class="card-link float-end delete">Delete</a>
            </div>
          </div>
        </div>`);
    });
  }
}

function handleUserQuotaCheck(el, e) {
  const quota = pageType === "microgrids" ? quotas.grid : quotas.sizingdoe;
  const dataName = "grid";
  userQuotaCheck(grids.length, dataName, quota);
};

async function create(e) {
  e.preventDefault();
  let newGrid = {};
  newGrid['name'] = $('#new-grid-modal #grid-name').val();
  newGrid['description'] = $('#new-grid-modal #grid-description').val();
  newGrid['isSizingTemplate'] = pageType === "microgrids" ? 0 : 1;

  const res = await postData("grids_add", "#new-grid-form", newGrid);

  if (!res.error) {
    $('#new-grid-modal').modal('hide');
    displayToastMessage("New grid created!");
    buildTab();
  }

}

async function deleteGrid(e) {
  const gridId = $(e.target).data('id');
  const res = await postData("grids_remove", null,  {id: gridId});

  if (!res.error) {
    closeConfirmDeleteModal(e);
    $('#confirm-delete-grid-modal').modal('hide');
    displayToastMessage('Grid successfully deleted.');
    buildTab();
  }

}

function openConfirmDelete(e) {
  e.preventDefault();
  const gridId = e.target.dataset.id;
  const grid = grids.find(d => d.id == gridId);
  $('#confirm-delete-grid-modal .grid-name').text(grid.name);
  $('#delete-grid-btn').data('id', gridId);
  $('#delete-grid-btn').on('click', deleteGrid);
  $('#confirm-delete-grid-modal').modal('show');
}

function clearNewGridFields () {
  $('#new-grid-form #grid-name').val('');
  $('#new-grid-form #grid-description').val('');
}