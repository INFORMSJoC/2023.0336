function formatDataListAsDict(dataArr, columnKeys, maxRows) {
  let dictList = [];
  if (maxRows && maxRows < dataArr.length) {
    dataArr = dataArr.slice(0, maxRows);
  }
  dataArr.forEach((row) => {
    const dict = {};
    row.forEach((value, i) => {
      dict[columnKeys[i]] = value;
    });
    dictList.push(dict);
  });
  return dictList;
}

function isFloat(n) {
  return Number(n) === n && n % 1 !== 0;
}

// Formats numeric value to display in table
function formatValue(value) {
  if (isFloat(value)) {
    var log10 = value ? Math.floor(Math.log10(value)) : 0,
      div = log10 < 0 ? Math.pow(10, 1 - log10) : 100;
    value = Math.round(value * div) / div;
  }
  return value;
}

// The table generation function
function tabulate(data, columnKeys, columnLabels, roundDecimals = true) {
  if (data.length > 0 && !columnKeys) {
    columnKeys = Object.keys(data[0]);
  }

  if (!columnLabels) {
    columnLabels = columnKeys;
  }

  return `
    <table class="table table-bordered table-hover">
      <thead>
        <tr>
          ${columnLabels
            .map((l) => {
              return `<th>${l}</th>`;
            })
            .join("")}
        </th>
      </thead>
      <tbody>
      ${data
        .map((d) => {
          return `
          <tr>
            ${columnKeys
              .map((k, i) => {
                const value = roundDecimals ? formatValue(d[k]) : d[k];
                return `<td ${
                  i % 2 !== 0 ? "class='right'" : ""
                }>${value}</td>`;
              })
              .join("")}
          </tr>
        `;
        })
        .join("")}
      </tbody>
    </table>
  `;
}

// Takes uri and desires filename and opens a download window
function saveAs(uri, filename) {
  try {
    // Create a new XMLHttpRequest
    var xhr = new XMLHttpRequest();
    xhr.open("GET", uri, true);
    xhr.responseType = "blob";

    xhr.onload = function () {
      if (xhr.status === 200) {
        var blob = xhr.response;
        var link = document.createElement("a");
        link.href = window.URL.createObjectURL(blob);
        link.download = filename;

        // Append link to the body (required for Firefox)
        document.body.appendChild(link);

        // Programmatically click the link to trigger the download
        link.click();

        // Remove the link from the document
        document.body.removeChild(link);

        console.log("Download started: " + filename);
      } else {
        console.error("Failed to fetch file: " + xhr.statusText);
      }
    };

    xhr.onerror = function () {
      console.error("Network error while attempting to download file.");
    };

    // Send the request
    xhr.send();
  } catch (error) {
    // Provide error feedback
    console.error(
      "An error occurred while attempting to download the file:",
      error
    );
  }
}

// Takes a click event and elId, saves the table within elId as a CSV
function exportTable(elId, filename) {
  const fileNameCorrected = sanitizeFilename(filename);
  const csv = $(elId).table2csv("return", { quoteFields: false });
  const file =
    "data:text/csv;filename=da.txt;charset=UTF-8," + encodeURIComponent(csv);
  saveAs(file, fileNameCorrected);
}

// Takes a results array from the API response and maps it out in a table
async function mapResultsData(results, pageName) {
  // Add href tags around items that need links, returns array of promises
  const resultsWithLinks = results.map(async (r) => {
    const id = r.id;
    const resultLink =
      ["simulate"].indexOf(pageName) !== -1
        ? `/tools/${pageName}/compute/?id=${id}`
        : `/tools/${pageName}/results/${id}`;
    const locationRes = await postData("locations_get", null, {
      id: r.locationId,
    });
    const urlParams = new URLSearchParams(window.location.search);
    const hasAll = urlParams.has("all");
    const role = $("#role").text();
    let mappedResult = {
      "Result ID":
        r.success === null ? r.id : `<a href="${resultLink}">${r.id}</a>`,
      Microgrid: r.gridName,
      "Energy Management System": r.energyManagementSystemName,
      Powerload: r.powerloadName,
      Location: `${locationRes.data.name}, ${locationRes.data.region}, ${locationRes.data.country}`,
      "Simulation Start": r.startdatetime,
      "Simulation End": r.enddatetime,
      Completed: formatResultsStatus(r.success),
    };

    if (role !== "Guest") {
      const canShow = r.success !== null || hasAll || role === "Admin";
      mappedResult["Delete"] = canShow
        ? `<a href="#" data-id="${id}" data-page="${pageName}" data-name="result" onclick="handleOpenConfirmDeleteResult(event)">Delete</a>`
        : "";
    }

    if (pageName === "resilience") {
      mappedResult["Disturbance"] = r.name;
      mappedResult["Disturbance Start"] = r.disturbanceDatetime;
      mappedResult["Repair"] = "TBD";
      mappedResult["Extend Timeframe (proportion)"] = r.extendTimeframe;
    }

    // For debugging purposes
    if (hasAll) {
      mappedResult["Run Submit Time"] = r.runsubmitdatetime;
      mappedResult["Run Start Time"] = r.runstartdatetime;
      mappedResult["Run End Time"] = r.runenddatetime;
      mappedResult["Compute Job ID"] = r.computeJobId;
    }

    return mappedResult;
  });
  $("#results").html("");
  if (results.length > 0) {
    let results = await Promise.all(resultsWithLinks).then((data) => data);
    let keys = Object.keys(results[0]);
    const table = tabulate(results, keys, null, false);
    $("#results").append(table);
  } else {
    $("#results").text("You don't have any results yet.");
  }
  $("#full-screen-loader").hide();
}
