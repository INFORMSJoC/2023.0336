
disturbanceData = Object();
componentTypes = {};
grids = [];
powerloads = [];
graphs = {};

buildTab();


async function buildTab() {
  grids = await getData("grids_get");
  powerloads = await getData("powerloads_get");
  componentTypes = await getData("component_types");

  graphs = buildGraphs($("#simulateD3Row"), componentTypes);
  // buildLocationInputs();
  const gridsWithComponents = grids.filter(grid => grid.components.length > 0);

  populateDropdown($("#simulateGridSelection"), gridsWithComponents)
  populateDropdown($("#simulatePowerloadSelection"), powerloads)

  initCalendar($("#simulatestartdatetime"));

  // passing no arguments to refreshPlots() will hide it.
  refreshPlots(null, $("#simulateD3Row"), componentTypes, graphs);

  // // Used to be in a now absent callback for changing global load scale property (also absent)
  // refreshPowerloads(tab_name)

  $("#simulate-form :input").change(() => {
    $(`#simulateD3Row`).hide();
  });
}

// Handles "Update Simulation" button click
async function runSimulation(e) {
  e.preventDefault();

  $("#simulation-run-btn").hide();
  $("#simulation-load-btn").show();

  const data = getValuesFromForm($("#simulate-form"));

  const res = await postData("simulate", null, data);
  
  if (!res.error) {
    refreshPlots(res.data.output, $("#simulateD3Row"), componentTypes, graphs);    
  }

  $("#simulation-load-btn").hide();
  $("#simulation-run-btn").show();
}
