# General Information

This repository contains a rudimentary *django project* (named `django_project`) and an almost empty example *app* (called `mainapp`). It is based on <https://djangoforbeginners.com/hello-world/>.

**Features:**
- Working HTML template with associated files for CSS and JavaScript.
- Basic unittest
- Rudimentary debugging infrastructure based on [ipydex](https://github.com/cknoll/ipydex) 

This django project should simplify and speed up getting started with a new project.

Nevertheless, if you have never used django before, working through the [django tutorial](https://docs.djangoproject.com/en/3.1/intro/tutorial01/) is highly recommended. 

# Local Testing Deployment
- Clone the repo
- Activate an appropriate environment (venv, conda)
- Run `pip install -r requirements.txt`
- Initialize the database `python manage.py migrate`
- Run the unittests with `python manage.py test --rednose` 
- Start the test server with `python manage.py runserver`


# Deployment on Remote Server
- to be added
