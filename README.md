## Install
Install python3 and pip3 packet manager first.
Then go to the project directory and run commands:
```
pip3 -r requirements.txt
./manage.py migrate
```
Then open file settings_private.py in editor and fill it with actual settings.
There your LJR username and password, SMTP settings and some spam filter settings.

## Usage: 
```
python3 filter.py
```
There should be an environment variable set before usage: DJANGO_SETTINGS_MODULE=comments_filter.settings.
