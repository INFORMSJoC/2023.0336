repairs = [];
componentTypes = {};
quotas = [];
currentRepair = null;

buildTab();

// Add modal event listeners
$("#new-repair-modal").on("hide.bs.modal", resetNewRepairModal);

async function buildTab() {   
  repairs = await getData("resilience_repairs_get");     
  componentTypes = await getData("component_types");  
  quotas = await getData("quota");  
  buildList();
  buildNewRepairComponentTypeInputs();
}

function handleUserQuotaCheck (e) {
  userQuotaCheck(repairs.length, "repair", quotas.repair);
}

function buildNewRepairComponentTypeInputs() {
  Object.keys(componentTypes).forEach(ctId => {
    const componentType = componentTypes[ctId];
    $("#new-repair-component-types").append(`
      <label class="form-label">${componentType.description}</label>
      <input 
        class="form-control" 
        data-name="${ctId}"
        type="number"  
        min="0.1"
        max=""
        step=".01" 
        required="true"
        value=""
        onkeyup="validateMaxMinInput(this, event)" 
        onkeypress="validateMaxMinInput(this, event)">
      </input>
    `)
  })

}

function resetNewRepairModal(e) {
  $(':input','#new-repair-form').not(':button, :submit').val('')
}

function buildList() {
  const numRepairs = repairs.length;
  $("#repairs-title").text(`${numRepairs} Repair${numRepairs > 1 ? "s" : ""}`);

  $('#repair-main-view').show();
  $('#repair-edit-view').hide();
  $("#repairs-list").empty();

  if (repairs.length === 0) {
    $('#no-repairs-message').show();
  }

  else {
    
    if (repairs.length === 0) {
      $('#no-repairs-message').show();
    }

    else {
      $('#no-repairs-message').hide();
      // Map out grids using Bootstrap cards
      repairs.forEach(repair => {
        const card = `
          <div class="col">
            <div class="card repair-card inline-card" id="repair-card-${repair.id}">
              <div class="repair-header card-header d-flex justify-content-between align-items-baseline"> 
                <div id="repair-name-container-${repair.id}"></div>
              </div>
              <div class="card-body">
                <div id="repair-description-container-${repair.id}"></div>
                <br/>
                <div id="repairs-component-types-list-${repair.id}"></div>
                <a href="#" id="repair-${repair.id}-open-confirm-delete-btn" data-id="${repair.id}" class="card-link float-end delete">Delete</a>
              </div>
            </div>
          </div>
        `;
  
        $("#repairs-list").append(card);

        const componentTypeList = Object.keys(componentTypes).map(ctId => {
          const repairSpec = repair.specs.find(s => s.componentTypeId == ctId);
          return {
            id: ctId,
            value: repairSpec ? repairSpec.value : undefined,
            minVal: 0.1,
            maxVal: null,
            name: componentTypes[ctId].description
          }
        });

        createFormWithEvents(repair.id, `#repair-name-container-${repair.id}`, repair.name, saveNameDescription, "name");
        createFormWithEvents(repair.id, `#repair-description-container-${repair.id}`, repair.description, saveNameDescription, "description");
        createFormWithEvents(repair.id, `#repairs-component-types-list-${repair.id}`, null, saveAttributes, "list", componentTypeList, "Mean times to repair (hours)")
        $(`#repair-${repair.id}-open-confirm-delete-btn`).on('click', openConfirmDelete);
      });

      
    }

  }
}

function openConfirmDelete(e) {
  e.preventDefault();
  // Attach component id to bootstrap modal
  const repairId = e.target.dataset.id;
  const repair = repairs.find(r => r.id == repairId);
  $('#confirm-delete-repair-modal .repair-name').text(repair.name);
  $('#delete-repair-btn').data('id', repairId);
  $('#delete-repair-btn').on('click', deleteRepair)
  $('#confirm-delete-repair-modal').modal('show');
}

async function saveRefresh() {
  displayToastMessage("Repair saved.");
  repairs = await getData("resilience_repairs_get");
  buildList();
}

async function create(e) {
  e.preventDefault();
  const formVals = getValuesFromForm("#new-repair-form");
  let data = {name: formVals.name, description: formVals.description, attributes: []};
  delete formVals.name;
  delete formVals.description;
  data.attributes = formVals;

  const res = await postData("resilience_repairs_add", "#new-repair-form", data);

  if (!res.error) {
    $('#new-repair-modal').modal('hide');
    saveRefresh();
  }

}

async function deleteRepair(e) {
  const repairId = $(e.target).data('id');
  const res = await postData("resilience_repairs_remove", `#repair-card-${repairId} .card-body`, { id: repairId });
  if (!res.error) {
    closeConfirmDeleteModal(e);
    saveRefresh();
  }
}

async function saveAttributes(e) {
  e.preventDefault();
  const repairId = e.target.dataset.id;
  const formVals = getValuesFromForm(e.target);
  const data = {id: repairId, attributes: formVals}
  const res = await postData("resilience_repairs_update_attributes", `#repair-card-${repairId} .card-body`, data);

  if (!res.error) {
    saveRefresh();
  }

}

async function saveNameDescription(e) {
  e.preventDefault();
  const repairId = e.target.dataset.id;
  const formVals = getValuesFromForm(e.target);
  formVals.id = repairId;

  const res = await postData("resilience_repairs_update_name_description", `#repair-card-${repairId} .card-body`, formVals);

  if (!res.error) {
    saveRefresh();
  }

}


