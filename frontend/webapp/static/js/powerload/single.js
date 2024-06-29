currentPowerload = null;
const powerloadId = $("meta[name='id']").attr("content");

build(true);

// TODO: Refactor this, shares lots of code with grid page
async function build(buildGraphTable) {
  res = await postData("powerloads_get", null, { id: powerloadId });
  if (res.error) return;
  currentPowerload = res.data;

  $("#name-container").empty();
  $("#description-container").empty();

  createFormWithEvents(
    currentPowerload.id,
    "#name-container",
    currentPowerload.name,
    "name",
    null,
    null,
    saveNameDescription
  );
  createFormWithEvents(
    currentPowerload.id,
    "#description-container",
    currentPowerload.description,
    "description",
    null,
    null,
    saveNameDescription
  );

  if (buildGraphTable) {
    const timeframe = getTimeFrameStringReadable(
      currentPowerload.startdatetime,
      currentPowerload.enddatetime
    );
    drawPowerloadTable();
    $("#power-vs-time-graph").append(
      `<div class="timeframe text-secondary">${timeframe}</div>`
    );
    buildGraphPowerloadApex({
      data: currentPowerload.data,
      width: 900,
      height: 500,
      strokeWidth: 2,
      name: currentPowerload.name,
      graphElId: "power-vs-time-graph",
    });
  }

  $("#full-screen-loader").hide();
  $("#tables").show();
}

function handleExportTable(e) {
  const dataType = e.target.dataset.type;
  exportTable(
    `#${dataType}-table-container table`,
    `${currentPowerload.name}-${dataType}-data`
  );
}

async function saveNameDescription(e) {
  e.preventDefault();
  const formVals = getValuesFromForm(e.target);
  formVals.id = currentPowerload.id;
  const res = await postData("powerloads_update", null, formVals);

  if (!res.error) {
    await build(false);
    displayToastMessage("Updates saved.");
  }

  containerEl.find(".edit-container").hide();
  containerEl.find(".display-container").show();
}

async function drawPowerloadTable() {
  const uploadedTableEl = $("#uploaded-table-container");
  const processedTableEl = $("#processed-table-container");
  const uploadedTable = tabulate(
    currentPowerload.data,
    ["startdatetime", "powerload_original"],
    ["Time", "Power (kW)"]
  );
  const processedTable = tabulate(
    currentPowerload.data.slice(0, -1),
    ["startdatetime", "middatetime", "enddatetime", "powerload"],
    ["Start Time", "Mid Time", "End Time", "Power (kW)"]
  );
  uploadedTableEl.append(uploadedTable);
  processedTableEl.append(processedTable);
}
