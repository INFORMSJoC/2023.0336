currentPowerload = null;
const powerloadId = $("meta[name='id']").attr("content"); 
const graph = buildGraphPowerload($("#powerVsTimeGraph"));

buildTab(true);

async function buildTab(buildGraphTable) {
  res = await postData("powerloads_get", null, {id: powerloadId});
  if (res.error) return;
  currentPowerload = res.data;
  $("#powerload-name-container form").data("id", currentPowerload.id);
  $("#powerload-name-container .display-container span").text(currentPowerload.name);
  $("#powerload-name-container .edit-container input").val(currentPowerload.name);
  $("#powerload-description-container form").data("id", currentPowerload.id);
  $("#powerload-description-container .display-container span").text(currentPowerload.description);
  $("#powerload-description-container .edit-container textarea").val(currentPowerload.description);
  if (buildGraphTable) {
    drawPowerloadTable(currentPowerload.data, "#powerload-table-container");
    drawPowerloadGraph(currentPowerload.data, "#powerVsTimeGraph")
  }
};

async function saveNameDescription(e) {
  e.preventDefault();
  const containerEl = $(`#powerload-${e.target.dataset.datatype}-container`);

  const formVals = getValuesFromForm(containerEl.find("form"));

  formVals.id = currentPowerload.id;
  const res = await postData("powerloads_update", null, formVals);
  
  if (!res.error) {
    await buildTab(false);
    displayToastMessage('Updates saved.');
  }

  containerEl.find(".edit-container").hide();
  containerEl.find(".display-container").show();

}

async function drawPowerloadGraph (dataset, graphElId) {
  $(graphElId).empty();
  refreshPlotPowerload(dataset, $(graphElId), graph);    
};

async function drawPowerloadTable (dataset, tableElId) {
  $(tableElId).empty();

  let powerloadAccessor =  (d) => + d ["powerload"];
  let timeAccessor =  (d) => d ['time'];

  dataset.forEach( function(d) {
    d.time = timeAccessor(d);
    d.power = powerloadAccessor(d);
  });

  // render the table        
  tabulate(dataset, ['time', 'power'], ["Time (hours)", "Power (kW)"], tableElId);

};
