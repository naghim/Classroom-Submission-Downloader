# Classroom Submission Downloader

Downloads all student submissions from a Google Classroom assignment.

# How to use

1. Create a Google Cloud API project.
2. Enable the [Google Classroom API](https://console.cloud.google.com/flows/enableapi?apiid=classroom.googleapis.com) and the [Google Drive API](https://console.cloud.google.com/flows/enableapi?apiid=drive.googleapis.com) on your Google Cloud API project.
3. Setup an OAuth 2.0 consent screen with the following scopes:

- classroom.courses.readonly
- classroom.coursework.students
- classroom.rosters.readonly
- drive.readonly

4. [Create OAuth 2.0 credentials](https://console.cloud.google.com/apis/credentials) and save the configuration as `credentials.json`.
5. Install Google API requirements for Python: `python -m pip install -r requirements.txt`
6. Run the project: `python download_submissions.py`
7. Log in with your Google account, choose a classroom, and choose the assignment to download.
