const setBranches = (reposWithBranches, repoURL) => {
  /*
   * Set Branches for a given Repo
   */
  const repo = reposWithBranches.find(r => r.url === repoURL)

  // clear current options
  $("#id_branch option").remove();

  const select = $("#id_branch");
  repo.branches.forEach(branch => {
    // Set master or main branches as the default selected option
    const selected = branch === "master" || branch === "main";
    select.append(new Option(branch, branch, selected, selected));
  })
};

$(document).ready(() => {
  const reposWithBranches = JSON.parse(document.getElementById('reposWithBranches').textContent);

  $("#id_repo").change((event) => setBranches(reposWithBranches, event.target.value));

  setBranches(reposWithBranches, $("#id_repo").val());
});
