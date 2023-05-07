from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
import json
import os

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.coursework.students',
    'https://www.googleapis.com/auth/classroom.rosters.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

## USER CACHE ##
user_cache_filename = 'user_cache.json'
user_cache = {}

if os.path.exists(user_cache_filename):
    with open(user_cache_filename, 'r', encoding='utf-8') as f:
        user_cache = json.load(f)

def write_user_cache():
    with open(user_cache_filename, 'w', encoding='utf-8') as f:
        json.dump(user_cache, f, ensure_ascii=False)

def login_to_classroom():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def choose_item(from_list):
    while True:
        try:
            result = int(input())

            if result >= 1 and result <= len(from_list):
                return from_list[result - 1]
        except:
            continue

def get_user_by_id(service, user_id):
    if user_id in user_cache:
        return user_cache[user_id]

    user = service.userProfiles().get(userId=user_id).execute()
    user_cache[user_id] = user
    write_user_cache()
    return user

def get_user_name(service, user_id):
    return get_user_by_id(service, user_id)['name']['fullName']

def view_courses(service):
    results = service.courses().list(pageSize=1000).execute()
    courses = results.get('courses', [])

    if not courses:
        print('No courses found.')
        return

    print('Which course would you like to access:')

    for i, course in enumerate(courses):
        name = course['name']
        print(f'{i + 1}. {name}')

    course = choose_item(courses)
    print('Chosen:', course['name'])
    return course

def view_course_works(service, course_id):
    results = service.courses().courseWork().list(courseId=course_id, pageSize=10000).execute()
    course_works = results.get('courseWork', [])

    if not course_works:
        print('No course works found.')
        return

    course_works.append({'title': 'All course works', 'return_all': True})

    print('Which course work would you like to access:')

    for i, course in enumerate(course_works):
        name = course['title']
        print(f'{i + 1}. {name}')

    course_work = choose_item(course_works)
    print('Chosen:', course_work['title'])

    if course_work.get('return_all', False):
        return course_works[:-1]

    return [course_work]

def download_file(request, full_filename, filename, user_name):
    with open(full_filename, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False

        while not done:
            status, done = downloader.next_chunk()
            print(f'Downloading {filename} from {user_name} ({int(status.progress() * 100)}%)...')

def download_submissions(service, drive_service, course, course_work):
    results = service.courses().courseWork().studentSubmissions().list(courseId=course_work['courseId'], courseWorkId=course_work['id'], pageSize=10000).execute()
    submissions = results['studentSubmissions']

    for submission in submissions:
        user_id = submission['userId']
        attachment_submission = submission['assignmentSubmission']
        user_name = get_user_name(service, user_id)

        if 'attachments' not in attachment_submission:
            print(f'Missing attachments from {user_name}')
            continue

        attachments = attachment_submission['attachments']
        folder_name = os.path.join('downloads', course['name'], course_work['title'], user_name)

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        for attachment in attachments:
            if list(attachment.keys()) != ['driveFile']:
                print('Unknown type found!')
                print(attachment.keys())
            
            if 'driveFile' not in attachment:
                continue
            
            drive_file = attachment['driveFile']
            drive_file_name = drive_file['title'].replace('/', '_')
            drive_file_id = drive_file['id']

            # This is where the file will be downloaded
            drive_file_full_name = os.path.join(folder_name, drive_file_name)

            if os.path.exists(drive_file_full_name) and os.path.getsize(drive_file_full_name) != 0:
                print(f'Skipping {drive_file_name} from {user_name} (already downloaded)')
                continue

            try:
                request = drive_service.files().get_media(fileId=drive_file_id)
                download_file(request, drive_file_full_name, drive_file_name, user_name)
            except HttpError as e:
                print('Cannot download file with Google Drive:', e)
                print('Attempting export...')
                
                request = drive_service.files().export_media(fileId=drive_file_id, mimeType='application/pdf')
                download_file(request, drive_file_full_name, drive_file_name, user_name)

def main():
    creds = login_to_classroom()

    try:
        service = build('classroom', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)

        course = view_courses(service)
        course_works = view_course_works(service, course['id'])

        for course_work in course_works:
            download_submissions(service, drive_service, course, course_work)
    except HttpError as e:
        print('An error occurred:', e)

if __name__ == '__main__':
    main()
