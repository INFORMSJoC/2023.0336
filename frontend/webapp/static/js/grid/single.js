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
$('#add-components-modal').on('hide.bs.modal', handleCloseComponentsModal);

build();

async function build() {
  components = await getData("components_get");
  componentTypes = await getData("component_types");
  buildGridView();
  $("#full-screen-loader").hide();
}

function createComponentList() {
  if (grid.components.length > 0) {
    $('#no-components-message').hide();
  }
  if (pageType === "microgrids") {
    createCompactComponentsList({
      components: grid.components, 
      allowEditQty: pageType === "microgrids",
      removeCallback: removeComponentFromGrid,
      removeText: "Remove"
    });
  } else {
    createComponentsListOnePerType();
  }
};

// Takes specs array and componentTypes and returns an array of objects 
// that contains specs and parameterTypes from componentTypes
function buildComponentSpecsWithParamType (specs, componentTypes) {
  const componentType = componentTypes[component.typeId];
  return specs.map(spec => {
    const ctSpec = componentType.specs.find(cts => cts.name === spec.name);
    return {...spec, parameterType: ctSpec.parameterType};
  });
}

async function buildGridView() {

  grid = await postData("grids_get", null, {"id": gridId});
  grid = grid.data
  
  $("#name-container").empty();
  $("#description-container").empty();
  createFormWithEvents(grid.id, "#name-container", grid.name, "name", null, null, saveNameDescription)
  createFormWithEvents(grid.id, "#description-container", grid.description, "description", null, null, saveNameDescription)

  if (grid.components.length > 0) {
    $("#stats").empty(); 
    const gridStatsHtml = createGridStats(grid);
    $("#stats").append(gridStatsHtml); 
    $("#stats").show(); 
  }

  if (grid.components.length === 0) {
    $("#stats").hide(); 
  }

  createComponentList();

}

async function saveNameDescription(e) {
  e.preventDefault();
  const formVals = getValuesFromForm(e.target);

  formVals.id = grid.id;
  const res = await postData("grids_update_name_description", "#content", formVals);
  
  if (!res.error) {
    // Update grids
    await buildGridView();
    // Update current grid data
    displayToastMessage('Updates saved.');
  }

  disableEdit(e);

}

// Builds list of components available to add to grid
function createAddComponentsList(componentTypeId) {
  const filteredComponents = (componentTypeId == null) ? components : components.filter(element => element.typeId.toString() === componentTypeId.toString());

  $('#add-components-modal .modal-body').empty();

  if ((componentTypeId == null && filteredComponents.length === grid.components.length) || (filteredComponents.length == 0)) {
    $('#add-components-modal .modal-body').append(`No components available.`);
  }

  // Only show components not currently added to the grid
  filteredComponents.forEach(component => {
    const gridHasComponent = grid.components.find(c => c.id == component.id);
    const added = newComponents.find(c => c.id == component.id);
    const componentSpecList = createCompactSpecList(component);

    function showAddedButton(added) {
      if (added) {
        return (
          `<button id="add-component-${component.id}-undo-btn" data-id="${component.id}" onclick="undoAddComponentTogrid(event)" class="btn btn-secondary btn-sm add-back-btn"">
              Remove &nbsp;<i class="bi bi-plus-circle"></i>
            </button>`
        )
      }
      else {
        return (
          `<button id="add-component-${component.id}-add-btn" data-id="${component.id}" onclick="addComponentToGrid(event)" class="btn btn-outline-success btn-sm add-back-btn"">
              Add &nbsp;<i class="bi bi-plus-circle"></i>
            </button>`
        )
      }
    }

    if (!gridHasComponent) {
      $('#add-components-modal .modal-body').append(`
          <div class="card component-card" id="add-component-card-${component.id}">
            <div class="status-message"></div>
            <div class="component-header card-header d-flex justify-content-between align-items-start">
              ${buildComponentHeader({component, showQuantity: false})}
              <div>
                ${showAddedButton(added)}
              </div>
            </div>
            <div class="card-body">
              <h5 class="card-title">Specifications</h5>
              <div class="spec-list">
                ${buildSpecList(componentSpecList)}
              </div>
              <div class="edit-button-container float-end">
              </div>
            </div>
          </div>
        `);

      }

    })

    if (newComponents.length > 0) {
      $('#add-components-to-btn').removeClass("btn-secondary");
      $('#add-components-to-btn').addClass("btn-primary");
    }

    else {
      $('#add-components-to-btn').addClass("btn-secondary");
      $('#add-components-to-btn').removeClass("btn-primary");
    }

};

function createComponentsListOnePerType() {
  $(`#components-accordion-left`).empty();
  $(`#components-accordion-right`).empty();
  if (Object.keys(componentTypes).length > 0) {
    $(`#no-components-message`).hide();
    counter = 0;
    for (const [componentTypeId, componentType] of Object.entries(componentTypes)) {
      componentFound = false
      counter = counter + 1
      grid.components.forEach((component, i) => {
        const componentSpecList = createCompactSpecList(component);
        if (component.typeId.toString() === componentTypeId) {
          $(`#components-accordion-${counter % 2 == 0 ? "left" : "right"}`).append(`
            <div class="accordion-item"> 
              <div class="component-header">
                ${buildComponentHeader({component, showQuantity: false})}
                <div class="component-qty-rmv-container d-flex justify-content-end">
                  <a href="#" id="remove-component-${component.id}-btn" onclick="removeComponentFromGrid(event)" class="float-end delete" data-id="${component.id}">
                    Remove <i class="bi bi-x-lg"></i>
                  </a>
                </div>
              </div>

              <div class="accordion-header" id="component-${component.id}-heading">
                <div class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#component-${component.id}-collapse" aria-expanded="true" aria-controls="panelsStayOpen-collapseOne">
                  View specs
                </div>
              </div>
            
              <div id="component-${component.id}-collapse" class="accordion-collapse collapse" aria-labelledby="#component-${component.id}-heading">
                <div class="accordion-body">
                  <div class="spec-list">
                    ${buildSpecList(componentSpecList)}
                  </div>
                </div>
              </div>
            </div>
          `);
          componentFound = true
        }
      });
      if (!componentFound) {
        $(`#components-accordion-${counter % 2 == 0 ? "left" : "right"}`).append(`
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
    $(`#no-components-message`).show();
  }

}

function showEditQuantity(e) {
  const componentId = e.target.dataset.id;
  $(`#edit-component-${componentId}-quantity-container`).show();
  $(`#display-component-${componentId}-quantity`).hide();
}

function cancelEditQuantity(e) {
  createComponentList();
  hideEditQuantity(e);
}

function hideEditQuantity(e) {
  const componentId = e.target.dataset.id;
  $(`#edit-component-${componentId}-quantity-container`).hide();
  $(`#display-component-${componentId}-quantity`).show();
}

async function saveComponentQuantity(e) {
  e.preventDefault();
  const componentId = e.target.dataset.id;
  const input = $(`#edit-quantity-${componentId}-input`);
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
  const res = await postData("grids_update_add_components", "#add-components-modal", componentData);

  if (!res.error) {
    buildGridView();
    displayToastMessage('Components added.');
    $("#add-components-modal").data("allowclose", "true");
    $('#add-components-modal').modal('hide');
    $("#add-components-modal").removeData("allowclose");
  }

}

function handleCloseComponentsModal(e) {
  if ($("#add-components-modal").data("allowclose")) {
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
  $('#add-components-modal').modal('show');
}
