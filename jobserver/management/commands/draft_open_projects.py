from open_projects_script import read_data


repo_url = "https://github.com/opensafely/disparities-comparison"
repo_branch = "main"


project_query = """
        SELECT DISTINCT w.name AS "Workspace Name", p.id AS "Project ID", p.name AS "Project name", p.status AS "Project Status", w.branch AS "Branch", r.url AS "Repo"
        FROM jobserver_workspace AS w
        INNER JOIN jobserver_project AS p ON (p.id = w.project_id)
        INNER JOIN jobserver_repo AS r ON (r.id = w.repo_id)
        INNER JOIN jobserver_jobrequest AS jr ON (w.id = jr.workspace_id)
        WHERE jr.created_at >= date_trunc('month', CURRENT_DATE - interval '3' MONTH)
        """
# print(read_data(project_query))

for i, project in enumerate(read_data(project_query)):
    print(f"\n\nRound{i}: \n\n{project['Project name']}\n{project['Repo']}")


# for project in read_data(project_query):
#     if project["Repo"] == repo_url and project["Branch"] == repo_branch:
#         get_tables(repo_url, repo_branch)
#         tables = get_tables(repo_url, repo_branch)
#         # print(tables)
#         project["TPP tables"] = tables
#         print(project)

# def write_table_to_csv(months, filename='output.csv'):
#     project_query = f"""
#         SELECT DISTINCT w.name AS "Workspace Name", p.id AS "Project ID", p.name AS "Project name", p.status AS "Project Status", w.branch AS "Branch", r.url AS "Repo"
#         FROM jobserver_workspace AS w
#         INNER JOIN jobserver_project AS p ON (p.id = w.project_id)
#         INNER JOIN jobserver_repo AS r ON (r.id = w.repo_id)
#         INNER JOIN jobserver_jobrequest AS jr ON (w.id = jr.workspace_id)
#         WHERE jr.created_at >= date_trunc('month', CURRENT_DATE - interval '{months}' MONTH)
#         """
#     table_rows = read_data(project_query)

#     if not table_rows:
#         print("No data to write")
#         return

#     with open(filename, 'w', newline='', encoding='utf-8') as f:
#         # Get column names from the first row
#         fieldnames = list(table_rows[0].keys())
#         writer = csv.DictWriter(f, fieldnames=fieldnames)

#         # Write header
#         writer.writeheader()

#         # Write all rows
#         writer.writerows(table_rows)

#     print(f"Table written to {filename}")
# # print(display_table(open_project_query))

# write_table_to_csv(5, 'projects_5_months.csv')
# write_table_to_csv(6, 'projects_6_months.csv')
# write_table_to_csv(7, 'projects_7_months.csv')
# write_table_to_csv(8, 'projects_8_months.csv')
# write_table_to_csv(9, 'projects_9_months.csv')
# write_table_to_csv(10, 'projects_10_months.csv')
# write_table_to_csv(11, 'projects_11_months.csv')
# write_table_to_csv(12, 'projects_12_months.csv')
# write_table_to_csv(18, 'projects_18_months.csv')
# write_table_to_csv(24, 'projects_24_months.csv')
# write_table_to_csv(30, 'projects_30_months.csv')
# write_table_to_csv(36, 'projects_36_months.csv')
