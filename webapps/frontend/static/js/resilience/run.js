
simulationResults = []
resilienceMetrics = Object()
resilienceParameters = Object()
disturbanceData = Object()  
quota = {};
componentTypes = {};
grids = [];
powerloads = [];
repairs = [];
disturbances = [];
graphs = {};

buildTab()

async function buildTab() {
  quota = await getData("quota");
  componentTypes = await getData("component_types");
  grids = await getData("grids_get");
  powerloads = await getData("powerloads_get");
  repairs = await getData("resilience_repairs_get");
  disturbances = await getData("resilience_disturbances_get");

  graphs = buildGraphs($("#resilienceD3Row"), componentTypes);
  //buildLocationInputs();
  const gridsWithComponents = grids.filter(grid => grid.components.length > 0);

  populateDropdown($("#resilienceGridSelection"), gridsWithComponents)
  populateDropdown($("#resiliencePowerloadSelection"), powerloads)
  populateDropdown($("#resilienceRepairSelection"), repairs)
  populateDropdown($("#resilienceDisturbanceSelection"), disturbances)

  initCalendar($(`#resiliencestartdatetime`));
  initCalendar($(`#resiliencedisturbance_datetime`));
  
  $("#resilience-form :input").change(() => {
    $(`#resilienceD3Row`).hide();
  });

  $("#resilience-num-runs").attr({max: quota.resilience_runs});
  $("#resilience-info-btn").on("click", () => $("#resilience-info-modal").modal("show"));
}

function buildTableWithDictionary(tableData, divID, optionalTableName) {
  let jqDiv = $("#"+divID+"")
  //let html = "<h1>"+optionalTableName+"</h1>"
  let html = "<div/>"+`<caption><h4>${optionalTableName}</h4></caption>`
  html+="<table class='table table-striped table-hover'>"
  for (let [key, value] of Object.entries(tableData)) {
    const regex = /^(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2})/;
    const dateMatch = value.toString().match(regex);

    if (dateMatch) {
      value = dateMatch[1];
    }

    else if (isNumeric(value)) {
      if (value.toString().includes(".")) {
        value = parseFloat(Number.parseFloat(value).toFixed(2));
      }
    }
    
    html+=`<tr><td>${key}</td><td>${value}</td></tr>`
  }
  html+="</table>"
  jqDiv.html(html)
};

async function runSimulation(e) {
  e.preventDefault();

  $("#resilience-run-btn").hide();
  $("#resilience-load-btn").show();

  const data = getValuesFromForm($("#resilience-form"));
  const res = await postData("resilience_compute_run", null, data);

  if (!res.error) {
    refreshPlots(res.data.output, $("#resilienceD3Row"), componentTypes, graphs)
  }

  $("#resilience-load-btn").hide();
  $("#resilience-run-btn").show();

}
