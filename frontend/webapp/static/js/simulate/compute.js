
let componentTypes = {};
const urlParams = new URLSearchParams(window.location.search);
let computeId = null;
let isFirstCheck = true;

const waitForResult = async (computeId, filename) => {
  const successRes = await postData("simulate_results_get", null, {id: computeId});
  if (successRes.data.success === null) {
    if (isFirstCheck) { createComputeTimeAlert() }
    isFirstCheck = false;
    setTimeout(async () => await waitForResult(computeId, filename), 15000);
  } 
  else if (successRes.data.success) {
    const computeRes = await postData("simulate_metrics_get", null, {id: computeId});
    buildAllApexCharts(computeRes.data.output, componentTypes, filename);
    displayStats(computeRes.data.summary_stats);
    resetButtons();
  }
  else {
    openAlert("danger", "#tool-error", "Simulation run failed. Please contact admin for more information.");
    resetButtons();
  }
};

const createComputeTimeAlert = () => {
  $("#simulation-message-container").append(`
    <div class="alert alert-success alert-dismissible fade show" role="alert">
      The simulation may take a few minutes to complete. If you navigate away from this page, the simulation will continue to run. When complete, the results will be accessible through your simulation history.
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
  `);
}

const build = async () => {
  componentTypes = await getData("component_types");
  let simRes = null;
  let locationRes = null;

  // Check for existing simulation
  if (urlParams.has("id")) {
    computeId = parseInt(urlParams.get("id"));
    simRes = await postData("simulate_results_get", null, {id: computeId});
    locationRes =  await postData("locations_get", null, {id: simRes.data.locationId});
  }

  await populateForm({
    isSizing: false,
    defaultSelections: simRes ? simRes.data : false,
    defaultLocations: locationRes ? locationRes.data : false,
  });

  if (computeId) {
    $("#compute-btn").click();
  }

};

const resetButtons = () => {
  $("#load-btn").hide();
  $("#compute-btn").show();
  const alertEl = $("#simulation-message-container .alert");
  if (alertEl) { alertEl.alert("close") }
};

const setButtonsLoading = () => {
  $("#compute-btn").hide();
  $("#load-btn").show();
};

// Handles "Update Simulation" button click
async function simulate(e) {
  e.preventDefault();
  setButtonsLoading();
  isFirstCheck = true;

  if (computeId) {
    const filename = createGraphFilenameFromForm($("#form"));
    waitForResult(computeId, filename);
    computeId = null;
  }

  else {
    // Delete urlParams
    if (urlParams.has("id")) {
      urlParams.delete("id");
      window.history.pushState({}, document.title, window.location.pathname);
    }
    const isValid = validateDateTimeInputs();
    if (isValid) {
      clearSimulationOutput();
      const filename = createGraphFilenameFromForm($("#form"));
      const formData = getValuesFromForm($("#form"));
      const dateTimeData = getDatesFromForm($("#form"));
      const simRes = await postData("simulate_compute", null, {...formData, ...dateTimeData});
      if (!simRes.error) {
        urlParams.set("id", simRes.data.compute_id);
        window.history.pushState({}, document.title, window.location.pathname + `?id=${simRes.data.compute_id}`);
        waitForResult(simRes.data.compute_id, filename);
      } else {
        resetButtons();
      }
    }
    else {
      resetButtons();
    }
  }
  
};

build();