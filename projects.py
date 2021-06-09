import csv


with open("workspaces.csv", "r") as f:
    reader = csv.reader(f)
    next(reader)

    workspaces = [r[0] for r in reader]
    start_count = len(workspaces)

    workspaces = set(workspaces)
    end_count = len(workspaces)

    if diff := end_count != start_count:
        print(f"Found {diff} duplicate workspace names")


with open("projects.md", "r") as f:
    lines = f.readlines()


def iter_lines(lines):
    for line in lines:
        if not line.startswith(" - "):
            continue

        line = line.removeprefix(" - ")
        workspace, _, _ = line.partition(",")

        yield workspace


organised_workspaces = list(iter_lines(lines))
seen = set()
for workspace in workspaces:
    if workspace in organised_workspaces:
        seen.add(workspace)


missing = workspaces - seen
if not missing:
    exit()

print("Missing Workspaces:")
for workspace in missing:
    print(f"- {workspace}")
