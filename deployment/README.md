# Deployment Information
## General

This directory contains a script and files to deploy the django application at an [uberspace](https://uberspace.de/) account (assuming no major changes).

We use [deploymentutils](https://codeberg.org/cknoll/deploymentutils) (which is built on top of  [fabric](https://www.fabfile.org/) (>=2.5). This decision seems to be a good compromise between raw bash scripts and a complex configuration management system like ansible – at least for python affine folks.
Complete deployment should (at best) be a onliner.


## How to deploy on a remote server ([uberspace](https://uberspace.de/)):

Note: We describe deployment on uberspace because from what we know it provides the lowest hurdle to test (and run) the application.

### Preparation

- Create an [uberspace](https://uberspace.de)-account (first month is free), then pay what you like.
- Set up your ssh key in the webfrontend
- Locally run `pip install deployment_requirements.txt`

### Deployment

- Create a file `config-production.ini` based on `config-example.ini`.
- Run `eval $(ssh-agent); ssh-add -t 5m` to unlock you private ssh-key in this terminal (The deplyment script itself does not ask for your ssh-key password).
- Run `python3 deploy.py remote`.
    - The script is mainly an automated version of this setup guide: <https://lab.uberspace.de/guide_django.html>.
- Run `python3 deploy.py --help` to see more options.
