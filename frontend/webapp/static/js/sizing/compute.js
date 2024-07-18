
componentTypes = {};

build();

async function build() {
  componentTypes = await getData("component_types");
  populateForm({isSizing: true});

  $("#sizing :input").change(() => {
    $(`#d3-row`).hide();
  });
}

async function simulate(e) {
  e.preventDefault();

  $("#compute-btn").hide();
  $("#load-btn").show();

  const isValid = validateDateTimeInputs();

  if (isValid) {
    const formData = getValuesFromForm($("#form"));
    const dateTimeData = getDatesFromForm($("#form"));
    const computeRes = await postData("sizing_compute", null, {...formData, ...dateTimeData});
    
    if (!computeRes.error) {
      if (computeRes.data.compute_job_id !== null) {
        displayToastMessage(`Job submitted with Slurm ID ${computeRes.data.compute_job_id}.`);
      }
      else {
        const message = `Analysis has previously been submitted with result ID ${computeRes.data.compute_id}.
        If you wish to recompute the analysis, first delete the existing result.`;
        openAlert("warning", "#warning-container", message);
      }
    }
  }

  $("#load-btn").hide();
  $("#compute-btn").show();

};
