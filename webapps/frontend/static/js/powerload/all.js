file = null
currentPowerload = null;
powerloads = [];
quotas = {};
timeArray = [];
valueArray = [];
fileUploadError = null;
const graph = buildGraphPowerload($("#powerVsTimeGraph"));

// Add bootstrap modal events
$("#new-powerload-modal").on("hide.bs.modal", resetNewModal);
buildList();

async function saveRefresh() {
  powerloads = await getData("powerloads_get");
  buildList();
}

function handleUserQuotaCheck(e) {
  userQuotaCheck(powerloads.length, "powerload", quotas.powerload);
}

async function buildList() {
  powerloads = await getData("powerloads_get");
  quotas = await getData("quota");

  const numPowerloads = powerloads.length;
  $("#powerloads-title").text(`${numPowerloads} Powerload${numPowerloads > 1 ? "s" : ""}`);

  currentPowerload = null;
  $('#powerload-main-view').show();
  $('#powerload-edit-view').hide();
  $("#powerloads-list").empty();

  if (powerloads.length === 0) {
    $('#no-powerloads-message').show();
  }

  else {
    
    if (powerloads.length === 0) {
      $('#no-powerloads-message').show();
    }

    else {
      $('#no-powerloads-message').hide();
      // Map out grids using Bootstrap cards
      powerloads.forEach(powerload => {
        const card = `
          <div class="col">
            <div class="card grid-card" style="width: 18rem;">
              <div class="card-body">
                <h5 class="card-title">${powerload.name}</h5>
                <div class="card-text description">${powerload.description}</div>
                <a href="${powerload.id}" id="powerload-${powerload.id}-edit-btn" data-id="${powerload.id}" class="card-link float-start">View</a>
                <a href="#" id="powerload-${powerload.id}-open-confirm-delete-btn" data-id="${powerload.id}" class="card-link float-end delete">Delete</a>
              </div>
            </div>
          </div>`;

        $("#powerloads-list").append(card);
        $(`#powerload-${powerload.id}-edit-btn`).on('click', openEdit);
        $(`#powerload-${powerload.id}-open-confirm-delete-btn`).on('click', openConfirmDelete);
      });
    }

  }
}

function handleUpload(e) {
  fileUploadError = null;
  const file = e.target.files[0];

  if (file) { 
    let reader = new FileReader();

    // Closure to capture the file information.
    reader.onload = ((readFile) => {
      return (e) => {
        const contents = e.target.result;
        let numCols = 2;
        let lines = contents.split(/\r\n|\n/);
        let splitLines = [];
        timeArray = [];
        valueArray = [];
        outerloop:
          for (let i = 0; i < lines.length; i++) {
            
            // Check for blank line and skip, if present
            if (lines[i] === "") { continue; }

            const splitLine = lines[i].split(",");

            // Check for missing value
            if (splitLine.length < numCols) {
              fileUploadError = `Row ${i + 1} is missing a value. Please make sure all rows contain 2 columns (time, power).`;
              break;
            } 
            
            for (let j = 0; j < numCols; j++) {
              
              if (!splitLine[j]) {
                fileUploadError = `Row ${i + 1}, column ${j + 1} is missing a value. Please make sure all rows contain 2 columns (time, power).`;
                break;
              }

              // Check for header and skip, if present
              if (i === 0 && isNaN(splitLine[j])) { continue outerloop; }

              // Check for NaN value
              if (isNaN(splitLine[j])) {
                fileUploadError = `Row ${i + 1}, column ${j + 1} contains a NaN value. Please make sure all rows (except the header) contain only integers.`;
                break;
              }
            }
            // record valid line
            splitLines.push(splitLine);
            timeArray.push(splitLine[0]);
            valueArray.push(splitLine[1]);
          }

        // Check for max rows
        if (valueArray.length > quotas.powerload_file_lines) {
          fileUploadError = `Length can not exceed ${quotas.powerload_file_lines} rows of data (excluding optional header, if present)`;
        }
        
        if (fileUploadError) {
          $("#powerload-preview").empty();
          openErrorAlert("#new-powerload-form", fileUploadError);
          timeArray = [];
          valueArray = [];
        }

        else {
          const columnKeys = ['time', 'power'];
          const dataset = formatDataListAsDict(splitLines, columnKeys, 15);
          tabulate(dataset, columnKeys, ["Time (hours)", "Power (kW)"], "#powerload-preview");
        }

      };
    })(file);

    reader.readAsText(file);
  }
};

function openEdit(e) {
  const id = e.target.dataset.id;

  // Set current powerload
  currentPowerload = powerloads.find((g) => {
    return g.id == id;
  });

  buildPowerloadView();
};

// Creates UI to edit a component
async function buildPowerloadView() {
  $('#powerload-main-view').hide();
  $('#powerload-edit-view').show();
  refreshNameDescription();
  const res = await postData("powerloads_get", null, {id: currentPowerload.id});
  if (res.error) return;
  const dataset = res.data;
  drawPowerloadTable(dataset, "#powerload-table-container");
  drawPowerloadGraph(dataset, "#powerVsTimeGraph")  
};

function refreshNameDescription() {
  $('#powerVsTimeGraph').empty();
  $('#powerload-description-container').empty();
  createFormWithEvents(currentPowerload.id, `#powerload-description-container`, currentPowerload.description, saveNameDescription, "description");
  createFormWithEvents(currentPowerload.id, `#powerload-name-container`, currentPowerload.name, saveNameDescription, "name");
};

function openPowerloadInfoModal(e) {
  $("#powerload-file-info-modal").modal("show");
};

function openConfirmDelete(e) {
  e.preventDefault();
  // Attach component id to bootstrap modal
  const powerloadId = e.target.dataset.id;
  const powerload = powerloads.find(pl => pl.id == powerloadId);
  $('#delete-powerload-btn').data('id', powerloadId);
  $('#confirm-delete-powerload-modal .powerload-name').text(powerload.name);
  $('#confirm-delete-powerload-modal').modal('show');
};

async function deletePowerload(e) {
  const id = $(e.target).data('id');
  const res = await postData("powerloads_remove", null, { id });
  if (!res.error) {
    // get updated powerloads
    await saveRefresh();
    closeConfirmDeleteModal(e);
  }
};

function resetNewModal(e) {
  $("#powerload-preview").empty();
  $('#new-powerload-form #powerload-name').val('');
  $('#new-powerload-form #powerload-description').val('');
  $('#new-powerload-form #powerload-file').val('');
  timeArray = [];
  valueArray = [];
  fileUploadError = null;
}

async function onUploadClicked(e) {
  e.preventDefault();

  $("#upload-btn").hide();
  $("#upload-load-btn").show();
  
  if (fileUploadError) {
    openErrorAlert("#new-powerload-form", fileUploadError);
  }

  else {
    const formVals = getValuesFromForm($("#new-powerload-form"));

    formVals.data = {
      "time": timeArray,
      "value": valueArray
    }

    const res = await postData("powerloads_add", "#new-powerload-error", formVals);
    
    if (!res.error) {
      await saveRefresh();
      $("#new-powerload-modal").modal("hide")
    }

  }

  $("#upload-load-btn").hide();
  $("#upload-btn").show();
  
};
