file = null
currentPowerload = null;
powerloads = [];
quotas = {};
timeArray = [];
valueArray = [];
fileUploadError = null;

// Add bootstrap modal events
$(`#new-modal`).on('hidden.bs.modal', handleCloseNewModal);
$("#confirm-delete-modal").on("hidden.bs.modal", closeConfirmDeleteModal)

buildList();

// Gets updated data, rebuilds powerload list
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
  $("#title").text(`${numPowerloads} Powerload${numPowerloads > 1 ? "s" : ""}`);

  currentPowerload = null;
  $("#list").empty();

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
        const timeframe = getTimeFrameStringReadable(powerload.startdatetime, powerload.enddatetime);
        $("#list").append(`
          <div class="widget">
            <h5>${powerload.name}</h5>
            <div class="card-body">
              <div>
                ${timeframe ? `<div class="text-secondary">${timeframe}</div>` : ""}
                <div class="card-text description">${powerload.description}</div>
                <img src="${powerload.image}"/>
              </div>
              <div>
                <a href="${powerload.id}" id="${powerload.id}-edit-btn" data-id="${powerload.id}" class="card-link float-start">View</a>
                <a href="#" id="${powerload.id}-open-confirm-delete-btn" data-id="${powerload.id}" class="card-link float-end delete">Delete</a>
              </div>
            </div>
          </div>
        `);
        $(`#${powerload.id}-open-confirm-delete-btn`).on('click', (e) => handleOpenConfirmDelete(e, powerload));
      });
    }

  }

  $("#full-screen-loader").hide();

}

function handleUpload(e) {

  // Empty table if values exist
  if (timeArray.length > 0 || valueArray.length > 0) {
    $("#preview").empty();
    timeArray = [];
    valueArray = [];
  }

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
            const date = new Date(splitLine[0]);
            const isBadDate = date.toString() === "Invalid Date";
            const isNotNum = isNaN(splitLine[1]);

            // Skip header if present
            if (i === 0 && isNotNum && isBadDate) { continue; }

            // Check for missing columns
            if (splitLine.length < numCols) {
              fileUploadError = `Row ${i + 1} is missing a value. Please make sure all rows contain 2 columns (time, power).`;
              break;
            } 
            
            // Check for missing column values
            for (let j = 0; j < numCols; j++) {
              if (!splitLine[j]) {
                fileUploadError = `Row ${i + 1}, column ${j + 1} is missing a value. Please make sure all rows contain 2 columns (time, power).`;
                break;
              }
            }

            // Check for date value in 1st col
            if (isBadDate) {
              fileUploadError = `Row ${i + 1}, column 1 is not a date. Please make sure all rows (except the header) contain a valid date.`;
              break;
            }

            // Check for NaN value in 2nd col
            if (isNotNum) {
              fileUploadError = `Row ${i + 1}, column 2 contains a NaN value. Please make sure all rows (except the header) contain only integers.`;
              break;
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
          $("#preview").empty();
          openAlert("danger", "#new-form", fileUploadError);
          timeArray = [];
          valueArray = [];
        }

        else {
          const columnKeys = ['time', 'power'];
          const dataset = formatDataListAsDict(splitLines, columnKeys, 15);
          let table = tabulate(dataset, columnKeys, ["Time", "Power (kW)"]);
          $("#preview").append('<span class="text-secondary">File contents (maximum of 15 rows shown)</span>');
          $("#preview").append(table);
        }

      };
    })(file);

    reader.readAsText(file);
  }
};

// Opens the confirm delete modal and displays additional information
async function handleOpenConfirmDelete(e, powerload) {
  openConfirmDeleteModal(e, powerload, deletePowerload);
  const results = await getData("sizing_results_get");
  const powerloadResults = results.filter(r => r["Powerload ID"] === powerload.id);

  if (powerloadResults.length > 0) {
    createRelatedDataList(
      powerloadResults, 
      "The following microgrid sizing results will also be deleted:", 
      "Result ID"
    )
  }

  $('#confirm-delete-modal').modal('show');

}

function openPowerloadInfoModal(e) {
  $("#file-info-modal").modal("show");
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

function handleCloseNewModal(e) {
  $("#preview").empty();
  timeArray = [];
  valueArray = [];
  fileUploadError = null;
  closeCreateNewModal(e);
};

async function onUploadClicked(e) {
  e.preventDefault();

  $("#upload-btn").hide();
  $("#upload-load-btn").show();
  
  if (fileUploadError) {
    openAlert("danger", "#new-form", fileUploadError);
  }

  else {

    const formVals = getValuesFromForm($("#new-form"));
    formVals.data = { "time": timeArray, "value": valueArray };

    const createRes = await postData("powerloads_add", "#new-error", formVals);

    if (!createRes.error) {

      const powerloadRes = await postData("powerloads_get", null, {id: createRes.data});

      if (!powerloadRes.error) {
        // Create hidden apex chart to create image
        const chart = buildGraphPowerloadApex({
          data: powerloadRes.data.data, 
          ...miniPowerloadDimensions,
          strokeWidth: 1,
          name: "",
          graphElId: "powerload-temp-graph"
        });
    
        const base64 = await chart.dataURI();

        // Send image
        const updateRes = await postData("powerloads_update", null, {id: createRes.data, image: base64.imgURI});

        if (!updateRes.error) {
          await saveRefresh();
          $("#new-modal").modal("hide")
        }

        chart.destroy();
        $("#powerload-temp-graph").empty();
      }

    }

  }

  $("#upload-load-btn").hide();
  $("#upload-btn").show();
  
};
