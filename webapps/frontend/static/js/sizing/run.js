
componentTypes = {};
grids = [];
powerloads = [];

buildTab();

async function buildTab() {
  grids = await getData("sizing_grids_get");
  powerloads = await getData("powerloads_get");
  componentTypes = await getData("component_types");

  // buildLocationInputs();
  const gridsWithComponents = grids.filter(grid => grid.components.length > 0);

  populateDropdown($("#gridSelection"), gridsWithComponents)
  populateDropdown($("#powerloadSelection"), powerloads)

  initCalendar($("#startdatetime"));

  // // Used to be in a now absent callback for changing global load scale property (also absent)
  // refreshPowerloads(tab_name)

  $("#sizing-form :input").change(() => {
    $(`#D3Row`).hide();
  });
}

// Handles "Update Simulation" button click
async function runSimulation(e) {
  e.preventDefault();

  $("#run-btn").hide();
  $("#load-btn").show();

  const data = getValuesFromForm($("#sizing-form"));

  const addRes = await postData("sizing_compute_add", null, data);

  if (!addRes.error && addRes.data[0]) {
    const runRes = await postData("sizing_compute_run", null, {id: addRes.data[0]});
    displayToastMessage(`Job submitted with Slurm ID ${runRes.data}.`);
  }

  $("#load-btn").hide();
  $("#run-btn").show();

}
