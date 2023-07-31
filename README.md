# Loading Data
`python3 manage.py extract_gdrive_files` can be run to retrive the csv files from google drive.

# API
- /trigger_report endpoint that will trigger report generation from the data provided (stored in DB)
    1. No input
    2. Output - report_id (random string)
    3. report_id will be used for polling the status of report completion
- /get_report endpoint that will return the status of the report or the csv
    1. Input - report_id
    2. Output
        - if report generation is not complete, return “Running” as the output
        - if report generation is complete, return “Complete” along with the CSV file with the schema described above.

# Testing
After cloning the repository, cd into the root folder and run this command `source ./run.sh`.
Wait for the Django test server to start.
Open a browser window and visit the url `http://localhost:8000/trigger_report`.
This returns a report_id. Visit this url (replacing the report_id query parameter with the obtained report_id)`http://localhost:8000/get_report?report_id=1`.
Repeat the last step until the status is returned as "Complete".

# Notes
Since this version is using an sqlite database, there might be an error: `OperationalError: database is locked`. This can be fixed my simply restarting the server. For deployment, this database can be replaced by a more scalable SQL database without any changes to the code. The only required changes for PostgresSQL would be installing the dabase and the database connector, and making changes to the DATABASES variable in store_monitor/settings.py file.
