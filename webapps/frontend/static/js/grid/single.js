let grid = null;
let newComponents = [];
let grids = [];
let quotas = [];
let components = [];
let componentTypes = [];
const gridId = $("meta[name='id']").attr("content"); 
const pageType = $("meta[name='page-type']").attr("content"); 
const pageTitle = pageType === "microgrids" ? "Microgrid" : "Microgrid Sizing Template";

// Add modal event listeners
$('#add-components-to-grid-modal').on('hide.bs.modal', handleCloseComponentsModal);

buildTab();

async function buildTab() {
  components = await getData("components_get");
  componentTypes = await getData("component_types");
  buildGridView();
}

async function buildGridView() {

  grid = await postData("grids_get", null, {"id":gridId});
  grid = grid.data
  $("#grid-name-container form").data("id", grid.id);
  $("#grid-name-container .display-container span").text(grid.name);
  $("#grid-name-container .edit-container input").val(grid.name);
  $("#grid-description-container form").data("id", grid.id);
  $("#grid-description-container .display-container span").text(grid.description);
  $("#grid-description-container .edit-container textarea").val(grid.description);

  if (pageType === "microgrids") {
    createComponentsList();
  } else {
    createComponentsListOnePerType();
  }

  if (grid.components.length > 0) {
    $('#grid-no-components-message').hide();
  }

}

async function saveNameDescription(e) {
  e.preventDefault();
  const containerEl = $(`#grid-${e.target.dataset.datatype}-container`);

  const formVals = getValuesFromForm(containerEl.find("form"));

  formVals.id = grid.id;
  const res = await postData("grids_update_name_description", "#grid-edit-view", formVals);
  
  if (!res.error) {
    // Update grids
    await buildGridView();
    // Update current grid data
    displayToastMessage('Updates saved.');
  }

  containerEl.find(".edit-container").hide();
  containerEl.find(".display-container").show();

}

// Builds list of components available to add to grid
function createAddComponentsList(componentTypeId) {

  const filteredComponents = (componentTypeId == null) ? components : components.filter(element => element.typeId.toString() === componentTypeId.toString());

  $('#add-components-to-grid-modal .modal-body').empty();

  if ((componentTypeId == null && filteredComponents.length === grid.components.length) || (filteredComponents.length == 0)) {
    $('#add-components-to-grid-modal .modal-body').append(`No components available.`);
  }

  // Only show components not currently added to the grid
  filteredComponents.forEach(component => {
    const gridHasComponent = grid.components.find(c => c.id == component.id);
    const added = newComponents.find(c => c.id == component.id);

    function showAddedButton(added) {
      if (added) {
        return (
          `<button id="grid-add-component-${component.id}-undo-btn" data-id="${component.id}" onclick="undoAddComponentTogrid(event)" class="btn btn-secondary btn-sm add-back-btn"">
              Remove &nbsp;<i class="bi bi-plus-circle"></i>
            </button>`
        )
      }
      else {
        return (
          `<button id="grid-add-component-${component.id}-add-btn" data-id="${component.id}" onclick="addComponentToGrid(event)" class="btn btn-outline-success btn-sm add-back-btn"">
              Add &nbsp;<i class="bi bi-plus-circle"></i>
            </button>`
        )
      }
    }

    if (!gridHasComponent) {
      $('#add-components-to-grid-modal .modal-body').append(`
          <div class="card component-card" id="grid-add-component-card-${component.id}">
            <div class="status-message"></div>
            <div class="component-header card-header d-flex justify-content-between align-items-start">
              ${buildComponentHeader(component)}
              <div>
                ${showAddedButton(added)}
              </div>
            </div>
            <div class="card-body">
              <h5 class="card-title">Specifications</h5>
              <div class="spec-list">
                ${buildComponentSpecList(component, componentTypes)}
              </div>
              <div class="edit-button-container float-end">
              </div>
            </div>
          </div>
        `);

      }

    })

    if (newComponents.length > 0) {
      $('#add-components-to-grid-btn').removeClass("btn-secondary");
      $('#add-components-to-grid-btn').addClass("btn-primary");
    }

    else {
      $('#add-components-to-grid-btn').addClass("btn-secondary");
      $('#add-components-to-grid-btn').removeClass("btn-primary");
    }

}


// Creates a list of grid's components on edit page
function createComponentsList() {
    $(`#grid-components-accordion-left`).empty();
    $(`#grid-components-accordion-right`).empty();
    if (grid.components.length > 0) {
      $(`#grid-no-components-message`).show();

      grid.components.forEach((component, i) => {
        $(`#grid-components-accordion-${i % 2 == 0 ? "left" : "right"}`).append(`
          <div class="accordion-item">
            
            <div class="grid-component-header">
              ${buildComponentHeader(component)}  
              
              <div class="grid-component-qty-rmv-container">
                <a href="#" id="remove-component-${component.id}-from-grid-btn" onclick="removeComponentFromGrid(event)" class="float-end delete" data-id="${component.id}">
                  Remove <i class="bi bi-x-lg"></i>
                </a>

                <div class="name-display" id="grid-display-component-${component.id}-quantity" data-id="${component.id}" style=display:${pageType === "microgrids" ? "block" : "none"};>
                  <span>Quantity: </span>
                  <span id="grid-edit-name-display">${component.quantity}</span>
                  <i id="grid-edit-component-${component.id}-quanity-btn" class="bi bi-pencil-square edit-pencil" onclick="showEditQuantity(event)" data-id="${component.id}"></i>
                </div>

                <div class="edit-name-container" data-id="${component.id}" id="grid-edit-component-${component.id}-quantity-container" style="display: none;">
                  <input id="grid-edit-quantity-${component.id}-input" type="number" class="form-control" value="${component.quantity}" min="1" max="20" step="1" onkeypress="validateMaxMinInputNoDecimal(this, event)" onkeyup="validateMaxMinInputNoDecimal(this, event)">
                  <button id="grid-save-component-${component.id}-quantity-btn" onclick="saveComponentQuantity(event)" class="btn btn-success btn-sm save" data-id="${component.id}">
                    <i class="bi bi-check2"></i>
                  </button>
                  <button id="grid-cancel-edit-component-${component.id}-quantity-btn" onclick="hideEditQuantity(event)" data-id="${component.id}" class="btn btn-secondary btn-sm cancel">
                    <i class="bi bi-x-lg"></i>
                  </button>
                </div>
              </div>
              
            </div>

            <div class="accordion-header" id="grid-component-${component.id}-heading">
              <div class="accordion-button component-header card-header grid-component-accordion-header" type="button" data-bs-toggle="collapse" data-bs-target="#grid-component-${component.id}-collapse" aria-expanded="true" aria-controls="panelsStayOpen-collapseOne">
                View specs
              </div>
            </div>
            
            <div id="grid-component-${component.id}-collapse" class="accordion-collapse collapse" aria-labelledby="#grid-component-${component.id}-heading">
              <div class="accordion-body">
                <div class="spec-list">
                  ${buildComponentSpecList(component, componentTypes)}
                </div>
              </div>
            </div>

          </div>
        </div>`);

    });
  }
  else {
    $(`#grid-no-components-message`).show();
  }

}

function createComponentsListOnePerType() {
  $(`#grid-components-accordion-left`).empty();
  $(`#grid-components-accordion-right`).empty();
  if (Object.keys(componentTypes).length > 0) {
    $(`#grid-no-components-message`).hide();
    counter = 0;
    for (const [componentTypeId, componentType] of Object.entries(componentTypes)) {
      componentFound = false
      counter = counter + 1
      grid.components.forEach((component, i) => {
        if (component.typeId.toString() === componentTypeId) {
          $(`#grid-components-accordion-${counter % 2 == 0 ? "left" : "right"}`).append(`
            <div class="accordion-item"> 
              <div class="grid-component-header">
                ${buildComponentHeader(component)}
                <div class="grid-component-qty-rmv-container">
                  <a href="#" id="remove-component-${component.id}-from-grid-btn" onclick="removeComponentFromGrid(event)" class="float-end delete" data-id="${component.id}">
                    Remove <i class="bi bi-x-lg"></i>
                  </a>
                </div>
              </div>

              <div class="accordion-header" id="grid-component-${component.id}-heading">
                <div class="accordion-button component-header card-header grid-component-accordion-header" type="button" data-bs-toggle="collapse" data-bs-target="#grid-component-${component.id}-collapse" aria-expanded="true" aria-controls="panelsStayOpen-collapseOne">
                  View specs
                </div>
              </div>
            
              <div id="grid-component-${component.id}-collapse" class="accordion-collapse collapse" aria-labelledby="#grid-component-${component.id}-heading">
                <div class="accordion-body">
                  <div class="spec-list">
                    ${buildComponentSpecList(component, componentTypes)}
                  </div>
                </div>
              </div>
            </div>
          `);
          componentFound = true
        }
      });
      if (!componentFound) {
        $(`#grid-components-accordion-${counter % 2 == 0 ? "left" : "right"}`).append(`
          <div class="accordion-item"> 
            <div class="add-type">
              <div class="row">
                <div class="col">
                  <img src="/static/images/${componentType.parameterName}.png"/>
                </div>
                <div class="col">
                  <button class="btn btn-primary float-end new"
                      data-component-type=${componentTypeId}
                      onclick="openAddComponentsToGridModal(event)">
                      + ${componentType.displayName}
                  </button>
                </div>
              </div>
            </div>
            <div class="add-type-buffer">
            </div>
          </div>
        `);
      }
    };
  }
  else {
    $(`#grid-no-components-message`).show();
  }

}

function showEditQuantity(e) {
  const componentId = e.target.dataset.id;
  $(`#grid-edit-component-${componentId}-quantity-container`).show();
  $(`#grid-display-component-${componentId}-quantity`).hide();
}

function hideEditQuantity(e) {
  const componentId = e.target.dataset.id;
  $(`#grid-edit-component-${componentId}-quantity-container`).hide();
  $(`#grid-display-component-${componentId}-quantity`).show();
}

async function saveComponentQuantity(e) {
  const componentId = e.target.dataset.id;
  const input = $(`#grid-edit-quantity-${componentId}-input`);
  const quantity = input.val();    
  const componentData = {id: grid.id, components: [{id: componentId, quantity}]};

  const res = await postData("grids_update_add_components", null, componentData);

  if (!res.error) {
    buildGridView(e);
    hideEditQuantity(e);
  }

}

async function addComponentsToGrid() {
  const componentData = {id: grid.id, components: newComponents};
  const res = await postData("grids_update_add_components", "#add-components-to-grid-modal", componentData);

  if (!res.error) {
    buildGridView();
    displayToastMessage('Components added.');
    $("#add-components-to-grid-modal").data("allowclose", "true");
    $('#add-components-to-grid-modal').modal('hide');
    $("#add-components-to-grid-modal").removeData("allowclose");
  }

}

function handleCloseComponentsModal(e) {
  if ($("#add-components-to-grid-modal").data("allowclose")) {
    return;
  }
  else {
    if (newComponents.length > 0) {
      if (confirm("You have unsaved changes, do you want to leave?") == true) {
        return;
      } else {
        e.preventDefault();
        return;
      }
    }
  }
}

function addComponentToGrid(e) {
  const componentId = e.target.dataset.id;
  newComponents.push({ id: componentId, quantity: 1 });
  if (pageType === "microgrids") {
    createAddComponentsList();
  } else {
    addComponentsToGrid(); // sizing template limits to 1 per type so add immediately
  }
}

function undoAddComponentTogrid(e) {
  const componentId = e.target.dataset.id;
  newComponents = newComponents.filter(c => c.id !== componentId);
  createAddComponentsList();
}

async function removeComponentFromGrid(e) {
  e.preventDefault();

  const componentId = e.target.dataset.id;
  const gridData = { id: grid.id, components: [componentId] }
  const res = await postData("grids_update_remove_components", null, gridData);

  if (!res.error) {
    buildGridView();
    displayToastMessage('Component removed');
  }

}

function openAddComponentsToGridModal(e) {
  newComponents = [];
  createAddComponentsList(e.target.getAttribute('data-component-type'));
  $('#add-components-to-grid-modal').modal('show');
}
