build();

async function build() {
  const results = await getData("sizing_results_get");
  await mapResultsData(results, "sizing");
}