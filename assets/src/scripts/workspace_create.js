const setBranches = (reposWithBranches, repoURL) => {
  /*
   * Set Branches for a given Repo
   */
  const repo = reposWithBranches.find((r) => r.url === repoURL);

  // clear current options
  const selectBox = document.getElementById("id_branch");
  while (selectBox.options.length > 0) {
    selectBox.remove(0);
  }

  const select = document.getElementById("id_branch");
  // biome-ignore lint/complexity/noForEach: update to biome v2
  repo.branches.forEach((branch) => {
    // Set master or main branches as the default selected option
    const selected = branch === "master" || branch === "main";
    select.append(new Option(branch, branch, selected, selected));
  });
};

const reposWithBranches = JSON.parse(
  document.getElementById("reposWithBranches").textContent,
);

document.getElementById("id_repo")?.addEventListener("change", (event) => {
  setBranches(reposWithBranches, event.target.value);
});
