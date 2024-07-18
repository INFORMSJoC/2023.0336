build();

async function build() {
  const results = await getData("simulate_results_get");
  await mapResultsData(results, "simulate");
}