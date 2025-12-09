# Toy example to check that tables are grouped into their correct projects
full_dict = [
    {"name": "opensafely"},
    {"name": "opensafely1"},
    {"name": "openprescribing"},
    {"name": "opensafely22"},
]

project_dict = {}
# {'name': 'opensafely', 'tables': {'clinical_events', 'parents'}}, {'name': 'openprescribing', 'tables': {'clinical_events', 'patients'}}


def get_tables(name):
    if name == "opensafely":
        table = {"clinical_events", "parents"}
    elif name == "openprescribing":
        table = {"clinical_events", "patients"}
    elif "opensafely" in name:
        table = None

    return table


for i, item in enumerate(full_dict):
    tables = get_tables(item["name"])

    existing_name = [
        project for project in project_dict.keys() if project in item["name"]
    ]

    key = item["name"]
    if tables and existing_name:
        merged_tables = project_dict[existing_name[0]] | tables
        project_dict[existing_name[0]] = merged_tables
    elif (not tables) and existing_name:
        print(f"\n\n existing name but no tables round{i}: \n\n{project_dict}")
        continue
    else:
        project_dict[key] = tables
    print(f"\n\nround{i}: \n\n{project_dict}")

print(project_dict)
