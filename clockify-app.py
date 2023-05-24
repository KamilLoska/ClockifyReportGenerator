import requests
import datetime
import csv
import os
import configparser

class ClockifyApp:

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        clockify_section = self.config['Clockify']
        self.API_KEY = clockify_section.get('API_KEY')
        self.WORKSPACE_ID = clockify_section.get('WORKSPACE_ID')
        self.USER_ID = clockify_section.get('USER_ID')
        self.BASE_URL = 'https://api.clockify.me/api/v1/'

        self.users = self.get_users_from_config()

    def get_time_entries_per_user(self, start_date, end_date):

        endpoint = f'workspaces/{self.WORKSPACE_ID}/user/{self.USER_ID}/time-entries'
        params = {
            'start': f'{start_date}T00:00:00Z',
            'end': f'{end_date}T23:59:59Z',
        }
        all_data = []
        page = 1

        while True:
            params['page'] = page
            response = self.send_get_request(endpoint, params)
            data = response
            all_data.extend(data)

            if len(data) == 0:
                break
            page += 1

        return all_data

    def get_users_from_config(self):
        users = {}
        for section in self.config.sections():
            if section.startswith('User'):
                user_id = self.config.get(section, 'ID')
                api_key = self.config.get(section, 'API_KEY')
                users[user_id] = api_key

        return users

    def generate_raport(self, date_from='', date_to=''):
        if not self.validate_date_format(date_from, date_to):
            print("Invalid date format. Please provide dates in the format 'YYYY-MM-DD'. ")
            return

        for user_id, api_key in self.users.items():
            self.API_KEY = api_key
            self.USER_ID = user_id
            get_data = self.get_time_entries_per_user(date_from, date_to)
            get_user_id, get_user_name = self.get_user_data()

            for data in get_data:
                create_date = data['timeInterval']['start'][:10]
                duration = data['timeInterval']['duration']
                name = data['description']
                if name == "":
                    name = "In progress..."

                if data['userId'] == get_user_id and date_from <= create_date <= date_to:
                    member_name = get_user_name

                    report_data = {
                        'Imię i nazwisko': " ".join(member_name.split(" ")[::-1]),
                        'Data': create_date,
                        'Czas trwania': self.format_duration(duration),
                        'Opis zadania': name,
                    }
                    print(report_data)

    def format_duration(self, duration):
        if duration != None:
            duration = duration[2:]
            hours = ""
            minutes = ""
            seconds = ""

            if "H" in duration:
                hours, duration = duration.split("H")
                hours += "H "
            if "M" in duration:
                minutes, duration = duration.split("M")
                minutes += "M "
            if "S" in duration:
                seconds, _ = duration.split("S")
                seconds += "S"

            formatted_duration = hours + minutes + seconds
            return formatted_duration.strip()

    def send_get_request(self, endpoint, params=None):
        headers = {
            'X-Api-Key': self.API_KEY,
            'Content-Type': 'application/json'
        }
        url = self.BASE_URL + endpoint
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        return data

    def get_user_data(self):
        endpoint = f'user'
        get_user_data = self.send_get_request(endpoint)
        return get_user_data['id'], get_user_data['name']

    def validate_date_format(self, first_date, second_date):
        try:
            datetime.datetime.strptime(first_date, '%Y-%m-%d')
            datetime.datetime.strptime(second_date, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def create_report(self, report_data):
        filename = 'report.csv'

        is_empty = os.stat(filename).st_size == 0
        if not is_empty:
            with open(filename, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row == report_data:
                        return

        with open(filename, 'a', newline='') as csvfile:
            fieldnames = ['Imię i nazwisko', 'Data', 'Czas trwania', 'Opis zadania']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if is_empty:
                writer.writeheader()
            writer.writerow(report_data)

        with open(filename, 'r') as csvfile:
            if csvfile.read().strip() == '':
                print(filename)
                return
