// Creates the component spec list in the body of expanded component accordions
const buildComponentSpecList = (component, componentTypes) => {
  const componentType = getComponentType(component.typeName, componentTypes);
  return (
    componentType.specs.map(spec => {
      return `<div class="spec-item"><b>${spec.name}</b>: ${component.attributes[spec.id]}</div>`;
    }).join('')
  )
}

// Takes a component and builds the header for the component accordion
const buildComponentHeader = (component) => {
  return (`
    <div class="d-flex justify-content-start align-items-end">
      <img src="/static/images/${component.typeName}.png"/>
      <div>
        <span>${component.name}</span>
        <br/>
        <div>
          <span class="text-secondary">${component.typeDescription}</span>
        </div>
      </div>
    </div>
  `);
}

// Takes a spec param name (typeParamName) and list of component types (componentTypes), 
// and returns the component type object that contains the param name
const getComponentType = (typeParamName, componentTypes) => {
  const componentTypeId = Object.keys(componentTypes).find(ct => {
    const componentType = componentTypes[ct];
    return componentType.parameterName === typeParamName;
  });
  return componentTypes[componentTypeId];
}

// Takes component type param name, list of component types, and spec param name 
// Returns the spec meta
const getSpecMetaFromComponentType = (componentTypeParamName, specParamName) => {
  const componentType = getComponentType(componentTypeParamName);
  const specId = Object.keys(componentType.specs).find(sKey => {
    return componentType.specs[sKey].parameterName === specParamName;
  });
  return componentType.specs[specId];
}

// converts an object of grid specifications to
// to a list of components which can in the same format as
// componentsTestData (i.e. [{'type':'', 'attributes':[...]}])
const specsToComponents = (specsObj, componentTypes) => {
  let componentsObj = {}
  for (const [key, value] of Object.entries(specsObj)) {
    let type = key;

    if (type) {
      if(!(type in componentsObj)){
        componentsObj[type] = {
          "typeName": type,
          "id": "rightsized_" + type,
          "name": "rightsized_" + type,
          "attributes": {}
        }
      }
      const specMeta = getSpecMetaFromComponentType(type, componentTypes, key);
      if (specMeta) {
        componentsObj[type]["attributes"][specMeta.id] = value;
      }
      else {
        console.log(`There was no spec meta found for paramName ${key} `)
      }
    }
  }

  let componentsList = []
  for (const [type, component] of Object.entries(componentsObj)) {
    componentsList.push(component)
  }
  return componentsList
}

// Gets value of cookie for input name
const getCookie = (name) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

const deleteCookie = (name) => {
  const cookie = getCookie(name);
  if (cookie) {
    document.cookie = `${name}= ; expires = Thu, 01 Jan 1970 00:00:00 GMT`
  }
}

const clearSession = () => {
  alert("Your authentication token has expired. You will now be redirected to login again.")
  window.location.replace(window.location.origin + URLS.clear_session);
};

// Performs get request and attaches JWT from cookie
// URL: The api endpoint URL (ex: /api/components/json)
// dataName: the name of the data to append/update to global data object (ex: "grids" will be appended to data.grids)
// type: request type (ex: "POST")
// postData: any data object to add to the request body
const apiReq = async (url, type, postData) => {
  // Get JWT from cookie
  const jwt = getCookie("jwt")
  const responseObj = {error: false, data: null};
  const defaultErrorMessage = "There was an error with the request.";

  try {
    const res = await $.ajax({
      async: true,
      url: URLS.server + url,
      type,
      beforeSend: (request) => {
        request.setRequestHeader("Authorization", "Bearer " + jwt);
      },
      data: JSON.stringify(postData),
      contentType:"application/json; charset=utf-8",
      dataType: "json"
    });

    if (res.processed) {
      responseObj.data = res.data;
    }
    else {
      responseObj.error = res.status_message ? res.status_message : defaultErrorMessage;
    }
  }
  catch (err) {
    if (err) {
      if (err.responseJSON) {
        if (err.responseJSON.message) {
          if (err.responseJSON.message === "API authentication token expired. Please log in again.") {
            return clearSession();           
          }
          else {
            responseObj.error = err.responseJSON.message;
          }
        }
      }
      else if (err && err.statusText.includes("NetworkError")) {
        responseObj.error = "Could not establish API connection (network)";
      }
      else if (err && err.status == 403) {
        responseObj.error = "Could not establish API connection (forbidden)";
      }
      else if (err && err.statusText) {
        responseObj.error = "API error: ".concat(err.statusText);
      }
      else {
        responseObj.error = "API error (see console log for details)";
      }
    }
    else {
      responseObj.error = defaultErrorMessage.concat(" API error (see console log for details)");
    }
  }

  return responseObj;
}

async function postData(dataName, elementId, data) {
  $("#loader").show();

  const res = await apiReq(URLS.api[dataName], "POST", data);
  
  if (res.error) {
    if (elementId) {
      openErrorAlert(elementId, res.error);
    }
    else {
      openErrorAlert("#tool-error", res.error);
    }
  }
  $("#loader").hide();
  return res;
}

async function getData(dataName, elementId) {
  $("#loader").show();
  const res = await apiReq(URLS.api[dataName], "GET");
  if (res.error) {
    openErrorAlert("#tool-error", res.error);
  }
  $("#loader").hide();
  return res.data;
}

// Closes a confirm delete modal
// Can only be called from an event handler (hence the event passed in parameter)
// Expects target element to have data-tabname property
const closeConfirmDeleteModal = (e) => {
  const tabName = e.target.dataset.tabname;
  $(`#delete-${tabName}-btn`).off();
  $(`#delete-${tabName}-btn`).unbind();
  $(`#delete-${tabName}-btn`).removeData();
  $(`#confirm-delete-${tabName}-modal`).modal('hide');
}

const closeConfirmSaveModal = (e) => {
  const tabName = e.target.dataset.tabname;
  $(`#save-${tabName}-btn`).off();
  $(`#save-${tabName}-btn`).unbind();
  $(`#save-${tabName}-btn`).removeData();
  $(`#confirm-save-${tabName}-modal`).modal('hide');
}

const closeCreateNewModal = (e) => {
  const tabName = e.target.dataset.tabname;
  $(`#new-${tabName}-specs`).empty();
  $(`#new-${tabName}-form`)[0].reset();
  $(`#new-${tabName}-modal`).modal('hide');
  $(`#new-${tabName}-error-alert`).hide();
}

const closeErrorAlert = (e) => {
  $(e.target).parent().remove();
}

const openErrorAlert = (parentElId, message) => {
  $(parentElId).append(`
    <div class="alert alert-danger alert-dismissible" role="alert">
      <span clas="text">${message}</span>
      <button type="button" class="btn-close" aria-label="Close" onClick="closeErrorAlert(event)"></button>
    </div>
  `);
};

// Displays a green toast in the bottom right-hand corner of screen
const displayToastMessage = (message) => {
  $('#global-toast .toast-text').text(message);
  $('#global-toast').toast('show');
};


// Takes a tabName (e.g. "simulate"), and returns an object of data from the tab's form.
const getValuesFromForm = (formEl) => {
  const _formInputEls = $(formEl).find(":input:not(:submit):input:not(:button)");
  let data = {};
  _formInputEls.each((i, el) => {
    const name = el.dataset.name;
    data[name] = el.value;
  });
  return data;
}

const preventDecimal = (el, e) => {
  // Ignore delete and backspace keys
  if (e.keyCode === 46) {
    e.preventDefault();
    return;
  }  
}

// Filters event to only allow numbers and decimals between min and max values
function validateMaxMinInput(el, e) {

  // Ignore delete and backspace keys
  if (e.keyCode != 46 && e.keyCode != 8) {

    // Check for valid number
    const validNum = new RegExp(/^\d*\.?\d*$/);
    if (!validNum.test(e.key)) {
        e.preventDefault();
        return;
    }
        
    // Check if next number is in min/max range
    if (el.min) {
      if (e.target.value && Number(e.target.value) < Number(el.min)) {
        e.preventDefault();
        alert("Value entered cannot be less than " + el.min);
        e.target.value = el.min;
      }
    }

    if (el.max) {
      if (e.target.value && Number(e.target.value) > Number(el.max)) {
        e.preventDefault();
        alert("Value entered cannot be more than " + el.max);
        e.target.value = el.max
      }
    }
  }
}

const validateMaxMinInputNoDecimal = (el, e) => {
  preventDecimal(el, e);
  validateMaxMinInput(el, e);
}

const enableEdit = (e) => {
  const parentEl = $(e.target).parent().parent();
  $(parentEl).find(".display-container").hide();
  $(parentEl).find(".edit-container").show();
};

const disableEdit = (e) => {
  const parentEl = $(e.target).parent().parent();
  $(parentEl).find(".display-container").show();
  $(parentEl).find(".edit-container").hide();
};

const createDescriptionEdit = (text) => {
  return (`
    <div class="description">
      <p style="margin-bottom: 5px;"><b>Description:</b> </p>
      <div class="display-container">
        <span>${text ? text : ""}</span>
        <i class="edit-pencil bi bi-pencil-square" onclick="enableEdit(event)"></i>
      </div>
      <div class="edit-container" style="display: none;">
        <textarea class="form-control" data-name="description" maxlength="128">${text ? text : ""}</textarea>
        <button type="submit" id="grid-save-description-btn" class="btn btn-success btn-sm save">
          <i class="bi bi-check2"></i>
        </button>
        <button type="button" class="btn btn-secondary btn-sm cancel" onclick="disableEdit(event)">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
    </div>
  `)
};

const createNameEdit = (text) => {
  return (`
    <div class="name">
      <div class="display-container">
        <span>${text}</span>
        <i class="edit-pencil bi bi-pencil-square" onclick="enableEdit(event)"></i>
      </div>
      <div class="edit-container" style="display: none;">
        <input class="form-control" value="${text}" data-name="name" maxlength="32"></input>
        <button type="submit" class="btn btn-success btn-sm save">
          <i class="bi bi-check2"></i>
        </button>
        <button type="button" class="btn btn-secondary btn-sm cancel" onclick="disableEdit(event)">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>     
    </div>
  `)
};

const createListEdit = (list, title, id) => {
  return (
    `<div class="list">

      <div class="display-container">
        <h5 class="card-title align-center">${title}</h5>
        <i class="bi bi-pencil-square edit-pencil" onclick="enableEdit(event)"></i>
        <br/>
        <div class="display-list d-flex align-content-around flex-wrap">
          ${list.map(item => {
            return `<div class="display-list-item"><b>${item.name}:</b> <span>${item.value}</span></div>`;
          }).join('')}
        </div>
      </div>

      <div class="edit-container" style="display: none;">
        <h5 class="card-title align-center">${title}</h5>
        <div class="editable-list">
            ${list.map(item => {
              const numberVal = Number(item.value);
              const nullValues = [NaN, null, undefined];
              return `<div class="editable-list-item">
                <b>${item.name}:</b> 
                <input 
                  class="form-control" 
                  type="number"
                  value="${Number.isNaN(numberVal) ? "" : item.value}" 
                  min="${nullValues.includes(item.minVal) ? "" : item.minVal}"
                  max="${nullValues.includes(item.maxVal) ? "" : item.maxVal}"
                  step="0.01"
                  data-title="spec"
                  required="true"
                  data-name="${item.id}" 
                  onkeyup="validateMaxMinInput(this, event)" 
                  onkeypress="validateMaxMinInput(this, event)">
                </input>
              </div>`;
            }).join('')}
          </div>
          <br/>
          <button class="btn btn-secondary" type="button" onclick="disableEdit(event)">Cancel</button>
          <button class="btn btn-success" type="submit" data-id="${id}">Save</button>
      </div>
    </div>`
  )
}

// Creates a form with an onsubmit event and a single input
// id: and ID that will be passed to the form's data-id attributes
// parentElId: the ID of the element the form will be placed
// text: the input's value
// submitCallback: the function to be called onSubmit
// type: either "name" or "description"
const createFormWithEvents = (id, parentElId, text, submitCallback, type, list, title) => {
  const $form = $(`<form data-id="${id}"></form>`);
  let element = null;

  if (type === "description") {
    element = createDescriptionEdit(text);
  }

  if (type === "name") {
    element = createNameEdit(text);
  }

  if (type === "list") {
    element = createListEdit(list, title, id)
  }

  $form.append(element);

  $form.submit((e) => {
    $(e.target).find(".display-container").show();
    $(e.target).find(".edit-container").hide();
    submitCallback(e);
  });

  $(parentElId).append($form);

};

const userQuotaCheck = (numItems, dataName, quota) => {
  if (numItems >= quota) {
    alert(`You have reached user account quota of ${quota} entries in ${dataName}s. To add a new ${dataName}, you will first need to delete one of your existing ${dataName}s.`);
    return;
  }

  $(`#new-${dataName}-modal`).modal("show");
}

const isNumeric = (str) => {
  if (typeof str === "number") return true;
  return !isNaN(str) && !isNaN(parseFloat(str));
}

// Handles collapsing/expanding main mobile navigation
const toggleMobileToolNavMenu = (el, e) => {
  const navMenu = $("#tool-navigation");
  if (navMenu.hasClass("show-nav-dropdown")) {
    navMenu.removeClass("show-nav-dropdown");
  }
  else {
    navMenu.addClass("show-nav-dropdown");
  }
}

const populateDropdown = (dropdownEl, dataArray) => {
  dataArray.forEach(item => {
    dropdownEl.append(new Option(item.name, item.id, false, false))
  })
}

const initCalendar = (calendarEl) => {
  calendarEl.datetimepicker({
    'lang': 'en',
    'step': 5,
    'format': 'Y-m-d H:i'
  }).datetimepicker('validate');
  return calendarEl;
}      