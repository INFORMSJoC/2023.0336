components = [];
componentTypes = {};
grids = [];
sizing = [];
defaultAddComponentErrorMsg = "There was an error adding this component";
// The component currently being edited
currentComponent = null;

//componentsToAdd = [];
//componentKeysToRemove = [];

buildTab();

// Add modal event listeners
//$(`#new-component-multi-modal`).on('hidden.bs.modal', resetMultiModal.bind(this));
$(`#new-component-modal`).on('hidden.bs.modal', closeCreateNewModal);
$("#confirm-delete-component-modal").on("hide.bs.modal", handleCloseConfirmDeleteModal)

// Creates a new component
async function create(e) {
  e.preventDefault();
  const formVals = getValuesFromForm($("#new-component-form"));

  let data = {
    name: formVals.name,
    description: formVals.description,
    type: formVals.type
  };

  delete formVals.name;
  delete formVals.description;
  delete formVals.type;
  data.attributes = formVals;

  const res = await postData("components_add", "#new-component-modal .modal-body", data);

  if (!res.error) {
    closeCreateNewModal(e);
    await updateList();
    displayToastMessage("New component created!")
  }
}

// Saves the name or description of a component
async function saveNameDescription(e) {
  e.preventDefault();
  const componentId = e.target.dataset.id;
  const formVals = getValuesFromForm(e.target);
  formVals.id = componentId;

  const res = await postData("components_update_name_description", `#component-card-${componentId}`, formVals);

  if (!res.error) {
    saveRefresh();
  }

}


// Saves a component's specs
async function saveSpecs(e) {
  e.preventDefault();
  const componentId = e.target.dataset.id;
  const formVals = getValuesFromForm(e.target);
  const specData = {id: componentId, attributes: formVals};
  const res = await postData("components_update_attributes", `#component-card-${componentId} .card-body`, specData);

  if (!res.error) {
    saveRefresh();
  }
}

// Deletes a component
async function deleteComponent(e) {
  const componentId = $(e.target).data('id');
  const res = await postData("components_remove", `#component-card-${componentId} .card-body`, {id: componentId});

  if (!res.error) {
    updateList();
    $('#confirm-delete-component-modal').modal('hide');
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
  const selectEl = $('#component-type-select');
  // Add to dropdown in new component form/dialog

  Object.keys(componentTypes).forEach((id) => {
    const displayName = componentTypes[id].displayName;
    const option = `<option value="${id}">${displayName}</option>`;
    selectEl.append(option);
  })
}

// Populates specs for new component based on selected type
function selectComponentType(e) {
    const specsEl = $(`#new-component-specs`);
    const typeId = e.target.value;
    const componentType = componentTypes[typeId];

    // Set component parameterName on select el
    specsEl.empty();

    componentType.specs.forEach(spec => {
        specsEl.append(`
            <label class="form-label">${spec.name}</label>
            <input 
              type="number" 
              min="${spec.minVal}" 
              max="${spec.maxVal ? spec.maxVal : ""}"
              step="0.01"
              class="form-control" 
              data-name="${spec.id}" 
              value="${spec.value ? spec.value : ""}" 
              required="true" 
              onkeyup="validateMaxMinInput(this, event)" 
              onkeypress="validateMaxMinInput(this, event)">
            </input>
        `)
    });
}

// Dismiss error alert in new component modal. Resets to default error message
function dismissAddComponentErrorAlert() {
    $('#new-component-error-alert').hide();
}

// Adds or updates a component in components and rebuilds component list UI
async function updateList() {
  components = await getData("components_get");
  buildList();
}

// Opens the confirm delete modal and displays additional information
function openConfirmDelete(e) {
  e.preventDefault(e);
  const componentId = e.target.dataset.id;
  const component = components.find(c => c.id == componentId);

  // Search for component in grid
  const gridsWithComponent = grids.filter(grid => {
    return grid.components.find(c => c.id == componentId);
  });

  $('#confirm-delete-component-modal .component-name').text(component.name);
  $('#delete-component-btn').data('id', e.target.dataset.id);
  $('#delete-component-btn').on('click', deleteComponent);

  if (gridsWithComponent.length > 0) {
    $('#confirm-delete-component-modal .modal-body').append(`
      <div class="grid-contains-components-warning">
        <p>The following microgrids contain this component and will be affected:</p>
        <ul>
          ${gridsWithComponent.map(grid => {
            return `<li>${grid.name}</li>`
          }).join('')}
        </ul>
      </div>
    `);
  }

  $('#confirm-delete-component-modal').modal('show');

}

// Removes component-specific information from the confirm delete modal before closing
function handleCloseConfirmDeleteModal(e) {
  $("#confirm-delete-component-modal .grid-contains-components-warning").remove();
}

// Switches between compact view
function handleCompactViewToggle(e) {
  if (e.target.checked) {
    $('#components-list').addClass('compact');
  }
  else {
    $('#components-list').removeClass('compact');
  }
}

// Gets all data needed for component tab to work, then builds UI
async function buildTab() {
  quotas = await getData("quota");
  components = await getData("components_get");
  componentTypes = await getData("component_types");
  grids = await getData("grids_get");
  sizing = await getData("sizing_grids_get");
  buildList();
  buildComponentTypeDropdown();
}

// Creates list of user's components from components data
function buildList() {

  const numComponents = components.length;
  $("#components-title").text(`${numComponents} Component${numComponents > 1 ? "s" : ""}`);
  $("#components-list").empty();

  if (components.length === 0) {
    $('#no-components-message').show();
  }

  else {
    $('#no-components-message').hide();

    // Map out Components using Bootstrap cards
    components.forEach(component => {   
      const componentCard = `
        <div class="col">
          <div class="card component-card inline-card" id="component-card-${component.id}">
            <div class="component-header card-header d-flex justify-content-between align-items-baseline"> 
              <div class="d-flex justify-content-start align-items-end">
                <img src="/static/images/${component.typeName}.png"/>
                <div>
                <div id="component-name-container-${component.id}"></div>
                <span class="text-secondary">${component.typeDescription}</span>
                </div>
              </div>
            </div>
            <div class="card-body">
              <div id="component-description-container-${component.id}"></div>
              <br/>
              <div id="component-spec-list-${component.id}" class="spec-list"></div>
              <a href="#" id="component-${component.id}-open-confirm-delete-btn" data-id="${component.id}" class="card-link float-end delete">Delete</a>
            </div>
          </div>
        </div>
      `
      $("#components-list").append(componentCard);
      $(`#edit-component-specs-${component.id}-form`).on("submit", saveSpecs);
      $(`#component-${component.id}-edit-btn`).on('click', enableEditSpecs);
      $(`#component-${component.id}-cancel-edit-btn`).on("click", disableEditSpecs);
      $(`#component-${component.id}-open-confirm-delete-btn`).on('click', openConfirmDelete);
    
      const componentSpecList = componentTypes[component.typeId].specs.map(spec => {
        return {
          id: spec.id,
          value: component.attributes[spec.id],
          minVal: spec.minVal,
          maxVal: spec.maxVal,
          name: spec.name
        }
      });

      createFormWithEvents(component.id, `#component-name-container-${component.id}`, component.name, saveNameDescription, "name");
      createFormWithEvents(component.id, `#component-description-container-${component.id}`, component.description, saveNameDescription, "description");
      createFormWithEvents(component.id, `#component-spec-list-${component.id}`, null, saveSpecs, "list", componentSpecList, "Specifications")

    });
  }

}

// Disableds editing a component's specs
function disableEditSpecs(e) {
  const componentId = e.target.dataset.id;
  const componentEl = $(`#component-card-${componentId}`);
  componentEl.removeClass("editable-card");
}

// Enables editing a component's specs
function enableEditSpecs(e) {
  const componentId = e.target.dataset.id;
  const component = components.find((component) => {
    return component.id == componentId;
  });

  currentComponent = JSON.parse(JSON.stringify(component));
  const componentEl = $(`#component-card-${componentId}`);
  componentEl.addClass("editable-card");
}

// Only allows typing component names with no spaces
function validateComponentName(el, e) {
  // const validRegex = new RegExp(/^\S*$/);
  const str = e.target.value;

  // // Disalow spaces and string greater than 64 chars
  if (e.key === " " || str.length > 64) {
      e.preventDefault();
  }

}