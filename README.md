[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CircleCI](https://circleci.com/gh/cknoll/markpad/tree/main.svg?style=shield)](https://circleci.com/gh/cknoll/markpad/tree/main)


# About markpad

markpad is a simple web application to display the content of etherpads interpreted as markdown source. It thus allows to combine the power of etherpads (author-colors, simple installation, variety of plugins, ...) with the aesthetics of markdown rendering.

markpad is free software and hosted on [codeberg](https://codeberg.org/cknoll/markpad) and [github](https://githubg.org/cknoll/markpad).


# Local Testing Deployment
- Clone the repo
- Activate an appropriate environment (venv, conda)
- Run `pip install -r requirements.txt`
- Create your configuration file (`config-production.ini`) from `deployment/config-example.ini`.
- Initialize the database:
    - `python manage.py makemigratins`
    - `python manage.py migrate`
- Run the unittests with `python manage.py test`
- Start the test server with `python manage.py runserver`


# Deployment on Remote Server

`deployment/deploy.py` is taylored towards deployment on [uberspace.de](https://uberspace.de).

See: [deployment/README.md](deployment/README.md).
