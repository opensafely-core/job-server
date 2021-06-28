const setBranches = (reposWithBranches, repoURL) => {
  /*
   * Set Branches for a given Repo
   */
  const repo = reposWithBranches.find((r) => r.url === repoURL);

  // clear current options
  $("#id_branch option").remove();

  const select = $("#id_branch");
  repo.branches.forEach((branch) => {
    // Set master or main branches as the default selected option
    const selected = branch === "master" || branch === "main";
    select.append(new Option(branch, branch, selected, selected));
  });
};

const reposWithBranches = JSON.parse(
  document.getElementById("reposWithBranches").textContent
);

document.getElementById("id_repo")?.addEventListener("change", (event) => {
  setBranches(reposWithBranches, event.target.value);
});

setBranches(reposWithBranches, document.getElementById("id_repo").value);
