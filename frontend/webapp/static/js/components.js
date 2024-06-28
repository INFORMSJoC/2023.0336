components = [];
componentTypes = {};
grids = [];
sizing = [];
defaultAddComponentErrorMsg = "There was an error adding this component";
// The component currently being edited
currentComponent = null;

build();
$(`#new-modal`).on('hidden.bs.modal', handleCloseCreateNewModal);
$("#confirm-delete-modal").on("hidden.bs.modal", closeConfirmDeleteModal)

// Creates a new component
async function create(e) {
  e.preventDefault();
  const formVals = getValuesFromForm($("#new-form"));
  let data = {
    name: formVals.name,
    description: formVals.description,
    type: formVals.type
  };

  delete formVals.name;
  delete formVals.description;
  delete formVals.type;
  data.attributes = formVals;

  const res = await postData("components_add", "#new-modal .modal-body", data);

  if (!res.error) {
    handleCloseCreateNewModal(e);
    await updateList();
    displayToastMessage("New component created!")
  }
}

function handleCloseCreateNewModal(e) {
  $(`#new-specs`).empty();
  closeCreateNewModal(e);
}

// Saves the name or description of a component
async function saveNameDescription(e) {
  const componentId = e.target.dataset.id;
  const formVals = getValuesFromForm(e.target);
  formVals.id = componentId;

  const res = await postData("components_update_name_description", `#card-${componentId}`, formVals);

  if (!res.error) {
    saveRefresh();
  }
};

// Saves a component's specs
async function saveAttributes(e) {
  const componentId = e.target.dataset.id;
  const formVals = getValuesFromForm(e.target);
  const specData = {id: componentId, attributes: formVals};
  const res = await postData("components_update_attributes", `#card-${componentId} .card-body`, specData);

  if (!res.error) {
    saveRefresh();
  }
};

async function deleteComponent(e) {
  const componentId = $(e.target).data('id');
  const res = await postData("components_remove", `#card-${componentId} .card-body`, {id: componentId});

  if (!res.error) {
    updateList();
    $('#confirm-delete-modal').modal('hide');
    displayToastMessage("Component successfully deleted.")
  }

}

// Updates the component list UI, displays toasts and resets currentComponent
function saveRefresh() {
  updateList();
  currentComponent = {};
  displayToastMessage("Component saved.")
}

// An in-between function for "userQuotaCheck" to allow the function to be called from the HTML file
function handleUserQuotaCheck(el, e) {
  userQuotaCheck(components.length, "component", quotas.components);
}

// Get component types and specs for each type
function buildComponentTypeDropdown() {    
  const selectEl = $('#type-select');
  // Add to dropdown in new component form/dialog

  Object.keys(componentTypes).forEach((id) => {
    const displayName = componentTypes[id].displayName;
    const option = `<option value="${id}">${displayName}</option>`;
    selectEl.append(option);
  })
};

// Populates specs for new component based on selected type
function selectComponentType(e) {
    const specsEl = $(`#new-specs`);
    const typeId = e.target.value;
    const componentType = componentTypes[typeId];
    // Set component parameterName on select el
    specsEl.empty();
 
    componentType.specs.forEach(spec => {
      specsEl.append(`<label class="form-label" for="spec-${spec.id}">${spec.name}</label>`)
      const inputHtml = createNumberInput(spec);
      specsEl.append(inputHtml);
    });
};

// Dismiss error alert in new component modal. Resets to default error message
function dismissAddComponentErrorAlert() {
  $('#new-error-alert').hide();
}

// Adds or updates a component in components and rebuilds component list UI
async function updateList() {
  components = await getData("components_get");
  if ($("#compact-view-input").is(":checked")) {
    buildCompactList();
  }
  else {
    buildList();
  }
}

// Opens the confirm delete modal and displays additional information
function handleOpenConfirmDelete(e) {
  const componentId = e.target.dataset.id;
  const component = components.find(c => c.id == componentId);

  openConfirmDeleteModal(e, component, deleteComponent);

  // Search for component in grid
  const gridsWithComponent = grids.filter(grid => {
    return grid.components.find(c => c.id == componentId);
  });

  if (gridsWithComponent.length > 0) {
    createRelatedDataList(
      gridsWithComponent, 
      "The following microgrids contain this component and will be affected:", 
      "name"
    );
  }

  $('#confirm-delete-modal').modal('show');

}

// Switches between compact view
function handleCompactViewToggle(e) {
  if (e.target.checked) {
    $("#list").hide();
    $("#components-compact-list").show();
    buildCompactList();
  }
  else {
    $("#list").show();
    $("#components-compact-list").hide();
    buildList();
  }
};

// Gets all data needed for component tab to work, then builds UI
async function build() {
  quotas = await getData("quota");
  components = await getData("components_get");
  componentTypes = await getData("component_types");
  grids = await getData("grids_get");
  sizing = await getData("sizing_grids_get");
  buildList();
  buildComponentTypeDropdown();
  $("#full-screen-loader").hide();
}

// Creates list of user's components from components data
function buildList() {

  const numComponents = components.length;
  $("#title").text(`${numComponents} Component${numComponents > 1 ? "s" : ""}`);
  $("#list").empty();

  if (components.length === 0) {
    $('#no-components-message').show();
  }

  else {
    $('#no-components-message').hide();

    // Map out Components using Bootstrap cards
    components.forEach(component => {   
      const componentCard = `
        <div class="card component-card" id="card-${component.id}">
          <div class="component-header card-header d-flex justify-content-between align-items-baseline"> 
            <div class="d-flex justify-content-start align-items-end">
              <img src="/static/images/${component.typeName}.png"/>
              <div>
              <div id="name-container-${component.id}"></div>
              <span class="text-secondary">${component.typeDescription}</span>
              </div>
            </div>
          </div>
          <div class="card-body">
            <div id="description-container-${component.id}"></div>
            <br/>
            <div id="spec-list-${component.id}" class="spec-list"></div>
            <a href="#" id="${component.id}-open-confirm-delete-btn" data-id="${component.id}" class="card-link float-end delete">Delete</a>
          </div>
        </div>
      `
      $("#list").append(componentCard);
      $(`#edit-specs-${component.id}-form`).on("submit", saveAttributes);
      $(`#${component.id}-edit-btn`).on('click', enableEditSpecs);
      $(`#${component.id}-cancel-edit-btn`).on("click", disableEditSpecs);
      $(`#${component.id}-open-confirm-delete-btn`).on('click', handleOpenConfirmDelete);
    
      const componentSpecList = componentTypes[component.typeId].specs.map(spec => {
        return {
          id: spec.id,
          value: component.attributes[spec.id],
          minVal: spec.minVal,
          maxVal: spec.maxVal,
          parameterType: spec.parameterType,
          name: spec.name
        }
      });

      createFullRowCardFormEvents(component, componentSpecList, "Specifications");

    });
  }

};

function buildCompactList() {
  createCompactComponentsList({
    components, 
    allowEditQty: false, 
    removeCallback: 
    handleOpenConfirmDelete, 
    removeText: "Delete"
  });
};

// Disableds editing a component's specs
function disableEditSpecs(e) {
  const componentId = e.target.dataset.id;
  const componentEl = $(`#card-${componentId}`);
  componentEl.removeClass("editable-card");
}

// Enables editing a component's specs
function enableEditSpecs(e) {
  const componentId = e.target.dataset.id;
  const component = components.find((component) => {
    return component.id == componentId;
  });

  currentComponent = JSON.parse(JSON.stringify(component));
  const componentEl = $(`#card-${componentId}`);
  componentEl.addClass("editable-card");
}