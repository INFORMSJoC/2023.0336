let disturbances = [];
let quotas = [];
let componentTypes = {};

buildTab();

// Add modal event listeners
$("#new-disturbance-modal").on("hide.bs.modal", resetNewDisturbanceModal);

async function buildTab() {
  disturbances = await getData("resilience_disturbances_get");
  componentTypes = await getData("component_types");
  quotas = await getData("quota");

  buildList();
  buildNewDisturbanceInputs();
}

function handleUserQuotaCheck() {
  userQuotaCheck(disturbances.length, "disturbance", quotas.disturbance)
}

function buildNewDisturbanceInputs() {
  Object.keys(componentTypes).forEach(ctId => {
    const componentType = componentTypes[ctId];
    $("#new-disturbance-component-types").append(`
      <label class="form-label">${componentType.description}</label>
      <input 
        class="form-control" 
        data-name="${ctId}"
        type="number" 
        step=".01" 
        min="0"
        max="1" 
        required 
        onkeyup="validateMaxMinInput(this, event)" 
        onkeypress="validateMaxMinInput(this, event)">
      </input>
    `)
  })

}

function resetNewDisturbanceModal(e) {
  $(':input','#new-disturbance-form').not(':button, :submit').val('')
}

function buildList() {
  const numDisturbances = disturbances.length;
  $("#disturbances-title").text(`${numDisturbances} Disturbance${numDisturbances > 1 ? "s" : ""}`);

  $('#disturbance-main-view').show();
  $('#disturbance-edit-view').hide();
  $("#disturbances-list").empty();

  if (disturbances.length === 0) {
    $('#no-disturbances-message').show();
  }

  else {
    
    if (disturbances.length === 0) {
      $('#no-disturbances-message').show();
    }

    else {
      $('#no-disturbances-message').hide();
      // Map out grids using Bootstrap cards
      disturbances.forEach(disturbance => {
        const card = `
          <div class="col">
            <div class="card disturbance-card inline-card" id="disturbance-card-${disturbance.id}">
              <div class="disturbance-header card-header d-flex justify-content-between align-items-baseline"> 
                <div id="disturbance-name-container-${disturbance.id}"></div>
              </div>
              <div class="card-body">
                <div id="disturbance-description-container-${disturbance.id}"></div>
                <br/>
                <div id="disturbances-component-types-list-${disturbance.id}"></div>
                <a href="#" id="disturbance-${disturbance.id}-open-confirm-delete-btn" data-id="${disturbance.id}" class="card-link float-end delete">Delete</a>
              </div>
            </div>
          </div>
        `;
  
        $("#disturbances-list").append(card);

        const componentTypeList = Object.keys(componentTypes).map(ctId => {
          const disturbanceSpec = disturbance.specs.find(s => s.componentTypeId == ctId);
          return {
            id: ctId,
            value: disturbanceSpec ? disturbanceSpec.value : undefined,
            minVal: 0,
            maxVal: 1,
            name: componentTypes[ctId].description
          }
        });

        createFormWithEvents(disturbance.id, `#disturbance-name-container-${disturbance.id}`, disturbance.name, saveNameDescription, "name");
        createFormWithEvents(disturbance.id, `#disturbance-description-container-${disturbance.id}`, disturbance.description, saveNameDescription, "description");
        createFormWithEvents(disturbance.id, `#disturbances-component-types-list-${disturbance.id}`, null, saveAttributes, "list", componentTypeList, "Chance of damage ([0, 1])")
        $(`#disturbance-${disturbance.id}-open-confirm-delete-btn`).on('click', openConfirmDelete);
      });

      
    }

  }
}

function openConfirmDelete(e) {
  e.preventDefault();
  const disturbanceId = e.target.dataset.id;
  const disturbance = disturbances.find(d => d.id == disturbanceId);
  $('#confirm-delete-disturbance-modal .disturbance-name').text(disturbance.name);
  $('#delete-disturbance-btn').data('id', disturbanceId);
  $('#confirm-delete-disturbance-modal').modal('show');
}

async function saveRefresh() {
  displayToastMessage("disturbance saved.");
  disturbances = await getData("resilience_disturbances_get");
  buildList();
}

async function create(e) {
  e.preventDefault();
  const formVals = getValuesFromForm("#new-disturbance-form");
  let data = {name: formVals.name, description: formVals.description, attributes: []};
  delete formVals.name;
  delete formVals.description;
  data.attributes = formVals;
  const res = await postData("resilience_disturbances_add", "#new-disturbance-form", data);

  if (!res.error) {
    $('#new-disturbance-modal').modal('hide');
    saveRefresh();
  }

}

async function deleteDisturbance(e) {
  const disturbanceId = $(e.target).data('id');
  const res = await postData("resilience_disturbances_remove", `#disturbance-card-${disturbanceId} .card-body`, { id: disturbanceId });
  if (!res.error) {
    closeConfirmDeleteModal(e);
    saveRefresh();
  }
}

async function saveAttributes(e) {
  e.preventDefault();
  const disturbanceId = e.target.dataset.id;
  const formVals = getValuesFromForm(e.target);
  const data = {id: disturbanceId, attributes: formVals}
  const res = await postData("resilience_disturbances_update_attributes", `#disturbance-card-${disturbanceId} .card-body`, data);

  if (!res.error) {
    saveRefresh();
  }

}

async function saveNameDescription(e) {
  e.preventDefault();
  const disturbanceId = e.target.dataset.id;
  const formVals = getValuesFromForm(e.target);
  formVals.id = disturbanceId;

  const res = await postData("resilience_disturbances_update_name_description", `#disturbance-card-${disturbanceId} .card-body`, formVals);

  if (!res.error) {
    saveRefresh();
  }

}


