// takes an array of json objects and converts to follow the golden rule of json
const categorizeOutput = (jsonArray, componentTypes) => {

  const timeFormat = "%Y-%m-%d %H:%M:%S"
  const timeParseFcn = d3.timeParse(timeFormat)

  let simulationOutputCategories = {
    "Powerload": "Powerload",
    "excess": "Excess Power",
    "stateOfCharge": "State of Charge"
  }

  Object.values(componentTypes).forEach(componentType => {
    simulationOutputCategories[componentType.parameterName] = componentType.displayName;
  });

  let goldenArray = new Array()
  jsonArray.forEach( d =>{
    if ("startDate" in d) {
      for (let field in simulationOutputCategories) {
        if (field in d) {                    
          goldenArray.push({
            "category": field, 
            "value": +d[field], 
            "startDate": timeParseFcn(d["startDate"])
          })
        }
      }
    }
  })
  return goldenArray;
};

const refreshPlots = (simulationValues, graphEl, componentTypes, graphs, hasDates=true, hasCategories=true) => {
  if (simulationValues) {
    graphEl.show();
    let currentSimulationData = categorizeOutput(simulationValues, componentTypes)
    for (let [key, graph] of Object.entries(graphs)) {
      graph.setData(currentSimulationData, hasDates, hasCategories)
    }                 
  }
  else{
    graphEl.hide();
  }
};

const refreshPlotPowerload = (simulationValues, graphEl, graph, hasDates=false, hasCategories=false) => {
  if (simulationValues) {
    graphEl.show();
    graph.setData(simulationValues, hasDates, hasCategories)
  }
  else{
    graphEl.hide();
  }
};

const graphDimensionsPowerload = {
  width: 750,
  height: 450,
  margin: {
    top: 30,
    bottom: 140,
    left: 100,
    right: 30
  }     
};

const graphDimensionsFull = {
  width: 750+90,
  height: 450,
  margin: {
    top: 20,
    bottom: 30,
    left: 100,
    right: 30+110
  }
};

const graphDimensionsHalf = {
  width: 750/2,
  height: 450/1.5,
  margin: {
    top: 30/2,
    bottom: 140, 
    left: 100,
    right: 30/2
  }
};

const graphOptionsPowerload = {
  elId: `#powerVsTimeGraph`,
  dimensionsIn: graphDimensionsPowerload,
  numXTicks: 7,
  legends: {"Powerload": ""},
  legendColors: {"Powerload": "orange"},
  xFieldStr: 'startDate',
  yFieldStr: 'Powerload',
  xLabelStr: 'Time (hours)',
  yLabelStr: 'Power (kW)'
};

const getGraphOptionsPower = (descriptions, colors) => {
  return {
    elId: `#powerVsTimeGraph`,
    dimensionsIn: graphDimensionsFull,
    numXTicks: 7,
    legends: descriptions,
    legendColors: colors,
    xFieldStr: 'startDate',
    yFieldStr: 'Powerload',
    xLabelStr: '',
    yLabelStr: 'Power (kW)'
  }
};

const graphOptionsExcessPower = {
  elId: `#excessPowerGraph`,
  dimensionsIn: graphDimensionsHalf,
  numXTicks: null,
  legends: {'excess': 'Unmet & Excess (kW)'},
  legendColors: {},
  xFieldStr: 'startDate',
  yFieldStr: 'excess',
  xLabelStr: '',
  yLabelStr: 'Unmet & Excess (kW)'
}

const graphOptionsChargeState = {
  elId: `#chargeStateGraph`,
  dimensionsIn: graphDimensionsHalf,
  numXTicks: null,
  legends: {"stateOfCharge": "State of Charge"},
  legendColors: {},
  xFieldStr: 'startDate',
  yFieldStr: 'stateOfCharge',
  xLabelStr: '',
  yLabelStr: 'State of Charge'
};

const buildGraphPowerload = (graphEl) => {
  graphEl.hide()
  return new LineGraph(graphOptionsPowerload)
};

const buildGraphs = (graphEl, componentTypes) => {
  // const datasetIn = d3.csv('data/tmp_data.csv',)
  // setup settings and descriptions        
  let simulationPowerDescriptions = {"Powerload": "Powerload"};
  let simulationPowerColors = {"Powerload": "orange"}

  Object.values(componentTypes).forEach((componentType) =>{
    simulationPowerDescriptions[componentType.parameterName] = componentType.displayName;
    simulationPowerColors[componentType.parameterName] = componentType.graphLineColor;
  });

  // hide this data at first
  graphEl.hide()

  return {
    'power': new LineGraph(getGraphOptionsPower(simulationPowerDescriptions, simulationPowerColors)),
    'excessPower': new LineGraph(graphOptionsExcessPower),
    'chargeState': new LineGraph(graphOptionsChargeState)
  }

};
