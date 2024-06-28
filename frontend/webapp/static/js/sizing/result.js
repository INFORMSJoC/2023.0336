computeId = null;
sizingGrids = [];
energyManagementSystems = [];

const saveColHeader = "Save to Components / Microgrids"
const urlParams = new URLSearchParams(window.location.search)
const query_string_all = urlParams.has('all');
const query_string_no_rounding = urlParams.has('precise');
const query_string_deficit = urlParams.get('deficit');
const deficitColumnLabel = `<div class="table-label-deficit" style="line-height: .75rem;"><span style="font-size: 11px;">(Set Limit:
          <a style="font-size: 11px;" href="#" id="deficit-link1" data-deficit="0.0">0.0 | </a>
          <a style="font-size: 11px;" href="#" id="deficit-link1" data-deficit="0.01">0.01 | </a>
          <a style="font-size: 11px;" href="#" id="deficit-link2" data-deficit="0.05">0.05 | </a>
          <a style="font-size: 11px;" href="#" id="deficit-link3" data-deficit="0.1">0.1</a>)<span></div> `;

build();

async function build() {
  computeId = $("#compute-id").text();
  document.getElementById("download-btn").dataset.computeid = computeId;
  sizingGrids = await postData("sizing_results_get", null, {"id":computeId, "display_all":query_string_all, "deficit_max":query_string_deficit});
 
  const resultsMeta = await getData("sizing_results_get");
  const metadata = resultsMeta.find(m => m.id == computeId);
  const startDate = new Date(metadata.startdatetime);
  const endDate = new Date(metadata.enddatetime);
  const timeframe = getTimeFrameStringReadable(startDate, endDate);
  const loadId = metadata.powerloadId;
  const gridId = metadata.gridId;
  const energyManagementSystemId = metadata.energyManagementSystemId;
  const gridRes = await postData("grids_get", null, {"id": gridId});
  const energyManagementSystems = await getData("energy_management_systems");
  const locationRes =  await postData("locations_get", null, {id: metadata.locationId});
  const location = locationRes.data;
  let powerloadRes = await postData("powerloads_get", null, {id: loadId});
  const energyManagementSystem = energyManagementSystems.find(ems => ems.id == energyManagementSystemId);
  powerloadRes.data.data = powerloadRes.data.data.filter(d => {
    const date = new Date(d.middatetime);
    return date >= startDate && date <= endDate;
  });
  createPowerloadWidget(powerloadRes.data, "#powerload", timeframe);
  createEnergyManagementSystemWidget(energyManagementSystem, "#energy-management-system", "Energy Management System");
  createGridWidget(gridRes.data, "#grid", "Microgrid Sizing Template");

  $("#full-screen-loader").hide();
  $("#location-name").append(`
    <b>Location: </b>: ${location.name}, ${location.region}, ${location.country}
  `);
  
  sizingGrids = sizingGrids.data;

  // Extract metricsSummaryStats
  sizingGrids = sizingGrids.map(sizingGrid => {
    const summaryStatsObj = JSON.parse(sizingGrid.metricsSummaryStats);
    Object.keys(summaryStatsObj).forEach(ssKey => {
      if (ssKey === "Contribution as a % of Total Energy") {
        const ppEnergy = summaryStatsObj[ssKey];
        Object.keys(ppEnergy).forEach(statKey => {
          sizingGrid[statKey] = ppEnergy[statKey];
        });
      }
      else {
        sizingGrid[ssKey] = summaryStatsObj[ssKey];
      }

    });
    delete sizingGrid.metricsSummaryStats;
    return sizingGrid;
  });

  // Create table headers
  if (sizingGrids.length > 0) {
    const sizingKeys = Object.keys(sizingGrids[0]);
    sizingKeys.splice(sizingKeys.indexOf("ID"), 1) // Remove ID from header (will be moved to front later)
    sizingKeys.splice(sizingKeys.indexOf("Name"), 1) // Remove Name from header
    sizingKeys.splice(sizingKeys.indexOf("Sizing Grid Deficit Ratio"),1) //remove from header so as to avoid duplicates
    columnKeys = ["ID", "Sizing Grid Deficit Ratio", ...sizingKeys, saveColHeader];
    };

  if (sizingGrids.length > 0) {
    console.log("sizing grids, column keys", sizingGrids, columnKeys)
    const table = tabulateSizingGrids(sizingGrids, columnKeys);
    $("#sizing-grids").append(table);
    $("#download-btn").show();
  }

  if (sizingGrids.length === 0) {
    $("#sizing-message").text("No microgrid designs found that meet power load requirements.")
  }

  if (metadata.success === null) {
    $("#sizing-message").text("Computations in progress. Please check back later.")
  }

  if (metadata.success === 0) {
    $("#sizing-message").text("Computations failed. Please contact admin for more information.")
  }
};

function openConfirmSave(e) {
  e.preventDefault();
  const sizingGridId = e.target.dataset.id;
  const sizingGrid = sizingGrids.find(sizingGrid => sizingGrid.ID == sizingGridId);
  $('#confirm-save-result-modal .record-name').text(sizingGrid.Name);
  $('#save-result-btn').data('id', sizingGridId);
  $('#confirm-save-result-modal').modal('show');
};

async function saveToAccount(e) {
  const sizingGridId = $(e.target).data('id');
  const res = await postData("sizing_results_save_to_grids", null,  {"id": computeId, "sizing_grid_id": sizingGridId});
  closeConfirmSaveModal(e);
  $('#confirm-save-result-modal').modal('hide');
  if (!res.error) {
    displayToastMessage('Sizing grid successfully saved to user-defined Components and Microgrids.');
  }
};

function handleExportTable (e) {
  exportTable('#rotated-table', `sizing-grids-result-${e.target.dataset.computeid}`);
};

// Creates a table with 45 degree rotated headers
function tabulateSizingGrids(grids, columnKeys) {
  $("#rotated-table").niceScroll({
    cursorminheight: 50,
    cursorwidth: "6px",
    autohidemode: false,
    cursorcolor: "#52637A",
    cursorborder: "0px",
  });

  grids.forEach((grid, gridIndex) => {
    let rowHtml = "";

    columnKeys.forEach((key, columnIndex) => {
      if (gridIndex === 0) {
            // Append ID first
            $("#rotated-table-headers thead tr").append(`
                <th><div class="rotate"><div class="fill"><div class="text">
                    ${statsToImageUrl[key] ? `<img src="${statsToImageUrl[key]}"/>` : ""}
                    ${key}
                </div></div></div></th>
            `)
            $("#rotated-table thead tr").append(`<th>${key === deficitColumnLabel ? "Sizing Grid Deficit Ratio" : key}</th>`);
        }

      if (key === saveColHeader) {
        rowHtml += '<td><a href="#" data-id="'+grid["ID"]+'" data-name="result" onclick="openConfirmSave(event)" class="card-link">Save</a></td>'
      }
      
      else {
        let val = grid[key] > .0001 ? formatValue(grid[key]) : 0;
        rowHtml += `<td>${val}</td>`
      }
    });

    $("#rotated-table tbody").append("<tr>" + rowHtml + "</tr>")
  });
};

//Functionality to add filter capabilities to grid deficit column using url parameters.
$(document).ready(function() {
    // Function to add parameters to URL
    function addParameterToURL(url, param, value) {
        // Split the URL into parts
        var urlParts = url.split('?');

        // Encode the value to ensure valid URL format
        var encodedValue = encodeURIComponent(value);

        // Check if there are query parameters already present
        if (urlParts.length >= 2) {
            // Remove existing parameter if it exists
            var params = urlParts[1].split('&');
            for (var i = params.length - 1; i >= 0; i--) {
                var keyValue = params[i].split('=');
                if (keyValue[0] === param) {
                    params.splice(i, 1);
                }
            }
            // Append the new parameter to the existing query string
            params.push(param + '=' + encodedValue);
            urlParts[1] = params.join('&');
        } else {
            // Create a new query string with the parameter
            urlParts.push(param + '=' + encodedValue);
        }

        // Combine the URL parts back to a single URL
        return urlParts.join('?');
    }

    // Get the current URL of the page
    var currentUrl = new URL(window.location.href);

    // Delegate event handling for dynamic links
    $(document).on('click', '[id^="deficit-link"]', function(event) {
        // Check if the link should be disabled
        if ($(this).hasClass('disabled')) {
            event.preventDefault(); // Prevent the default action of the link
            return; // Do nothing if the link is disabled
        }

        // Get the data attribute value
        var deficitValue = this.getAttribute('data-deficit');

        // Add or replace parameters in the URL
        var modifiedUrl = addParameterToURL(currentUrl.href, 'deficit', deficitValue);

        // Redirect to the modified URL
        window.location.href = modifiedUrl;
    });

    // Disable the active link
    if (query_string_deficit) {
        $('[data-deficit="' + query_string_deficit + '"]').addClass('disabled');
    } else {
        $('[data-deficit="0.0"]').addClass('disabled'); //defaults to this even on pageload w/o params
    }
});