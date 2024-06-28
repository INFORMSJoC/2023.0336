
// Track apex chart instances here
let apexCharts = {};
const powerloadGraphLineColor = "#FFA500";

// Empties and hides all chart containers
const clearCharts = () => {
  const chartIds = ["components-chart", "excess-power-chart", "charge-chart"];
  $("#chart-container").addClass("chart-hidden");
  chartIds.forEach(id => {
    if (apexCharts[id]) {
      // Destroy apex instance if it exists
      apexCharts[id].destroy();
      delete apexCharts[id];
    }
  });
};

const clearSummaryStats = () => {
  $("#stats-container .category").empty();
  $("#stats-container h5").remove();
  $("#stats-container").hide();
};

const clearSimulationOutput = () => {
  clearCharts();
  clearSummaryStats();
}

const miniPowerloadDimensions = {
  width: 388, 
  height: 220,
};

const apexTickOptions = {
  show: true,
  borderType: 'solid',
  color: '#545454',
};

const apexLabelStyles = {
  colors: "#000000",
  fontWeight: 200
};

const dateFormatter = (timestamp) => {
  const date = new Date(timestamp);
  return getDateString(date) + " " + getTimeString({date, withSeconds: false});
};

// Returns labels rounded to nearest 1-
const roundLabelsTo10 = (value) => {
  return Math.round(value / 10) * 10;
};

// Round labels to whole number
const roundLabels = (value) => {
  return value.toFixed();
}

// Round labels to 1 decimal place
const roundLabelsTo1Decimal = (value) => {
  return value.toFixed(1);
}

const buildGraphPowerloadApex = (options) => {
  let { data, width, height, strokeWidth, name, graphElId } = options;
  let categories = [];
  let series = {name: "Power (kW)", data: []};
  let filename = sanitizeFilename(name);

  // Organize data for apex charts
  data.forEach(d => {
    if (d.middatetime && isNumber(d.powerload)) {
      categories.push(d.middatetime);
      series.data.push(d.powerload);
    }
  });

  const chartOptions = {
    chart: {
      width,
      height,
      type: "line",
      animations: { enabled: false },
      zoom: { enabled: true },
      toolbar: {
        export: {
          csv: { dateFormatter, filename },
          png: { filename },
          svg: { filename }
        }
      }
    },
    tooltip: { enabled: false },
    colors: [powerloadGraphLineColor],
    series: [series],
    stroke: { width: [strokeWidth] },
    xaxis: {
      type: "datetime",
      categories,
      tickAmount: 5,
      axisTicks: apexTickOptions,
      title: {
        text: "Time",
        style: apexLabelStyles
      },
      labels: { 
        datetimeUTC: false,
        datetimeFormatter: { month: 'd MMM' } 
      }
    },
    yaxis: [{
      type: "numeric",
      title: {
        text: "Power (kW)",
        style: apexLabelStyles,
      },
      axisBorder: { show: true },
      axisTicks: apexTickOptions,
      forceNiceScale: true,
      decimalsInFloat: 0
    }],
  };
  
  const chart = new ApexCharts(document.getElementById(graphElId), chartOptions);
  chart.render();
  return chart;
};


// Takes data (directly from response of POST /simulate) and builds 3 charts (component, load, charge) using Apex charts
const buildAllApexCharts = (data, componentTypes, filename) => {
  let keys = ["stateOfCharge", "excess", "Powerload"];
  let series = {};
  let categories = [];
  let componentTypeDisplayNames = {};
  // Add powerload color first, since powerload is not in componentTypes
  let componentColors = [powerloadGraphLineColor]

  // Map component type display name to parameter name
  Object.keys(data[0]).forEach((key) => {
    const componentType = Object.values(componentTypes).find(ct => ct.parameterName === key);
    if (componentType) {
      // Add component type parameter names to keys for chart series
      keys.push(componentType.parameterName);
      componentColors.push(componentType.graphLineColor);
      componentTypeDisplayNames[componentType.parameterName] = componentType.displayName;
    }
  });

  data.forEach((d, i) => {
    // Push component types
    keys.forEach(k => {
      if (!series[k]) {
        const displayName = componentTypeDisplayNames[k] ? componentTypeDisplayNames[k] : k;
        series[k] = {data: [], max: d[k], min: d[k], displayName}
      }
      series[k].data.push(d[k]);
      // Track max/min values
      if (d[k] > series[k].max) {
        series[k].max = d[k];
      }
      if (d[k] < series[k].min) {
        series[k].min = d[k]
      }
    });
    categories.push(d.midDate);
  });

  let componentSeries = [];

  Object.keys(series).forEach((key, i) => {
    if (key !== "stateOfCharge" && key !== "excess") {
      componentSeries.push({
        name: series[key].displayName, 
        data: series[key].data, 
        borderColor: componentColors[i]
      });
    }
  });

  buildApexChart({
    series: componentSeries, 
    categories, 
    colors: componentColors, 
    elId: "components-chart", 
    yLabel: "Power (kW)",
    height: 470,
    width: 850,
    xAxisTickAmount: 7,
    xAxisType: "datetime",
    filename: filename + "_PowerVsTime",
    decimalsInFloat: 0
  });

  buildApexChart({
    series: [{name: "excess", data: series["excess"].data}], 
    categories, 
    colors: ["#000000"],
    elId: "excess-power-chart", 
    yMax: series["excess"].max, 
    yMin: series["excess"].min,
    yLabel: "Power (kW)",
    height: 210,
    width: 330,
    yAxisTickAmount: 3,
    xAxisTickAmount: 2,
    xAxisType: "datetime",
    filename: filename + "_excessPower",
    decimalsInFloat: 0
  });

  buildApexChart({
    series: [{name: "Charge", data: series["stateOfCharge"].data}], 
    categories, 
    colors: ["#000000"], 
    elId: "charge-chart", 
    yMax: 1, 
    yMin: 0, 
    yLabel: "BESS State of Charge",
    height: 210,
    width: 330,
    yAxisTickAmount: 2,
    xAxisTickAmount: 2,
    xAxisType: "datetime",
    filename: filename + "_stateOfCharge",
    decimalsInFloat: 1
  });

  $("#chart-container").removeClass("chart-hidden");

};

// Takes a series (https://apexcharts.com/docs/options/series/) of data, categories (array of dates)
// array of colors, and element ID. Places a chart inside of the elId element.
function buildApexChart(options) {
  let { 
    series, 
    categories, 
    colors, 
    elId,
    yMax,
    yMin,
    yLabel, 
    height, 
    width, 
    xAxisTickAmount,
    yAxisTickAmount,
    decimalsInFloat,
    xAxisType,
    filename
  } = options;

  // Special cases for straight lines (max and min are same value)
  if (isNumber(yMax) && isNumber(yMin) && (yMax === yMin)) {
    // If line is zero, add padding above and below
    if (yMax === 0) {
      yMax = 1;
      yMin = -1;
      yAxisTickAmount = 2;
    }
    // If line is any other number, add padding 1/2 of line value above and below
    else {
      yMax = yMax + (yMax / 2);
      yMin = yMin - (yMin / 2);
    }
  };


  var options = {
    chart: {
      height,
      width,
      type: "line",
      animations: { enabled: false },
      zoom: { enabled: true },
      toolbar: {
        export: {
          csv: { dateFormatter, filename },
          png: { filename },
          svg: { filename }
        }
      }
    },
    legend: { position: "right" },
    tooltip: { enabled: false },
    colors,
    series,
    stroke: { width: [2, 2] },
    xaxis: {
      type: xAxisType,
      categories,
      tickAmount: xAxisTickAmount,
      axisTicks: apexTickOptions,
      labels: { 
        datetimeUTC: false,
        datetimeFormatter: { month: 'd MMM' } 
      }
    },
    yaxis: [{
      type: "numeric",
      tickAmount: yAxisTickAmount ? yAxisTickAmount : undefined,
      axisBorder: { show: true },
      tickPlacement: "on",
      axisTicks: apexTickOptions,
      title: {
        text: yLabel,
        style: apexLabelStyles
      },
      // forceNiceScale: true,
      decimalsInFloat,
      min: isNumber(yMin) ? yMin : undefined,
      max: isNumber(yMax) ? yMax : undefined
    }],
    markers: categories.length === 1 ? {
      size: 5,
      colors,
      shape: "circle",
    } : {}
  };

  apexCharts[elId] = new ApexCharts(document.getElementById(elId), options);
  apexCharts[elId].render();

};
