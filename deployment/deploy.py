import time
import os
import re
import deploymentutils as du


from ipydex import IPS, activate_ips_on_exception

# simplify debugging
activate_ips_on_exception()


"""
This script serves to deploy and maintain the django application with which it is delivered.
It is largely based on this tutorial: <https://lab.uberspace.de/guide_django.html>.
"""


# call this before running the script:
# eval $(ssh-agent); ssh-add -t 10m


# -------------------------- Begin Essential Config section  ------------------------

# this file must be changed according to your uberspace accound details (machine name and user name)

config = du.get_nearest_config("config-production.ini")

remote = config("remote")
user = config("user")

# -------------------------- Begin Optional Config section -------------------------
# if you know what you are doing you can adapt these settings to your needs

# this is the root dir of the project (where setup.py lies)
# if you maintain more than one instance (and deploy.py lives outside the project dir, this has to change)
project_src_path = os.path.dirname(du.get_dir_of_this_file())

# base directory for local testing deployment
# might also be the place for a custom deploy_local.py script
local_deployment_workdir = "../../local_testing"

# directory for deployment files (e.g. database files)
deployment_dir = config("deployment_dir")

app_name = "mainapp"  # this is the name of the django app (not the project)

# name of the directory for the virtual environment:
venv = config("venv")

# -------------------------- End Config section -----------------------

# it should not be necessary to change the data below, but it might be interesting what happens.
# (After all, this code runs on your computer/server under your responsibility).

# because uberspace offers many pip_commands:
pipc = "pip3.8"

# this is only relevant if you maintain more than one instance
instance_path = os.path.join(du.get_dir_of_this_file(), "specific")

local_deployment_files_base_dir = du.get_dir_of_this_file()
repo_base_dir = os.path.split(local_deployment_files_base_dir)[0]


IPS()
exit()


du.argparser.add_argument("-o", "--omit-tests", help="omit test execution (e.g. for dev branches)", action="store_true")
du.argparser.add_argument("-d", "--omit-database",
                          help="omit database-related-stuff (and requirements)", action="store_true")
du.argparser.add_argument("-s", "--omit-static", help="omit static file handling", action="store_true")
du.argparser.add_argument("-x", "--omit-backup",
                          help="omit db-backup (avoid problems with changed models)", action="store_true")
du.argparser.add_argument("-p", "--purge", help="purge target directory before deploying", action="store_true")

args = du.parse_args()

final_msg = f"Deployment script {du.bgreen('done')}."

if args.target == "remote":
    # this is where the code will live after deployment
    target_deployment_path = f"/home/{user}/{deployment_dir}"
    static_root_dir = f"{target_deployment_path}/collected_static"
    debug_mode = False
    pip_user_flag = " --user"  # this might be dropped if we use a virtualenv on the remote target
    allowed_hosts = [f"{user}.uber.space"]
else:
    # settings for local deployment
    static_root_dir = ""
    target_deployment_path = os.path.join(local_deployment_workdir, deployment_dir)
    debug_mode = True
    pip_user_flag = ""  # assume activated virtualenv on local target
    allowed_hosts = ["*"]

pelican_content_src_dir = config("STATIC_HP_CONTENT_REPO").replace("__BASEDIR__", project_src_path)
pelican_content_dst_dir = os.path.dirname(config("STATIC_HP_CONTENT_REPO").
                                          replace("__BASEDIR__", target_deployment_path))

venv_dir = f"/home/{user}/{venv}"

# TODO
init_fixture_path = os.path.join(target_deployment_path, "fixitures/init_fixture.json")

# generate the uwsgi config file
tmpl_path = os.path.join("uberspace", "uwsgi", "apps-enabled", "template_pages.ini")
du.render_template(tmpl_path, context=dict(user=user, deployment_dir=target_deployment_path, venv_dir=venv_dir))

# generate the uwsgi ini-file
tmpl_path = os.path.join("uberspace", "etc", "services.d", "template_uwsgi.ini")
du.render_template(tmpl_path, context=dict(venv_abs_bin_path=f"%(ENV_HOME)s/{venv}/bin/"))


# TODO: make a backup of the remote-data
# print a warning for data destruction
du.warn_user(app_name, args.target, args.unsafe, deployment_path=target_deployment_path)


c = du.StateConnection(remote, user=user, target=args.target)


if args.initial:
    if not args.target == "remote":
        print("\n", du.bred("  The `--initial` option explicitly requires the target==`remote`"), "\n")
        exit()

    c.run(f"{pipc} install --user virtualenv")

    print("create and activate a virtual environment inside $HOME")
    c.chdir("~")

    c.run(f"rm -rf {venv}")
    c.run(f"virtualenv -p python3.7 {venv}")
    c.activate_venv(f"~/{venv}/bin/activate")

    # this was necessary to prevent errors on uberspace
    c.run(f"pip install --upgrade pip")
    c.run(f"pip install --upgrade setuptools")

    # ensure that the same version of deploymentutils like on the controller-pc is also in the server
    c.deploy_this_package()

    print("\n", "install uwsgi", "\n")
    c.run(f'pip install uwsgi', target_spec="remote")

    print("\n", "upload config files for initial deployment", "\n")

    srcpath1 = os.path.join(local_deployment_files_base_dir, "uberspace")
    srcpath2 = os.path.join(local_deployment_files_base_dir, "general")

    # upload config files to $HOME
    filters = "--exclude='README.md' --exclude='*/template_*'"
    c.rsync_upload(srcpath1 + "/", "~", filters=filters, target_spec="remote")
    c.rsync_upload(srcpath2 + "/", "~", filters=filters, target_spec="remote")

    c.run('supervisorctl reread', target_spec="remote")
    c.run('supervisorctl update', target_spec="remote")
    print("waiting 10s for uwsgi to start")
    time.sleep(10)

    res1 = c.run('supervisorctl status', target_spec="remote")

    assert "uwsgi" in res1.stdout
    assert "RUNNING" in res1.stdout

    c.run('uberspace web backend set / --apache', target_spec="remote")
    c.run('uberspace web backend set /d --http --port 8000', target_spec="remote")

    # note 1: the static files which are used by django are served under /static/ (not /d/static)
    # note 2: configuring apache to serve /static is not necessary (as already covered by /) but it does not harm
    c.run('uberspace web backend set /static --apache', target_spec="remote")

    # !!TODO:
    # erinnerung:
    # (vielleicht besser mit rsync und Zugangsbeschränkung)
    # um staging-Übersicht zu erzeugen habe ich bisher manuell eine entsprechende .htaccess-Datei abgelegt
    # https://support.tigertech.net/directory-index
    # run('echo "Options +Indexes" > /var/www.../staging/.htaccess'

    c.deactivate_venv()

if args.purge:
    if not args.omit_backup:
        print("\n", du.bred("  The `--purge` option explicitly requires the `--omit-backup` option. Quit."), "\n")
        exit()
    elif args.omit_database:
        print("\n", du.bred("  The `--purge` option conflicts  `--omit-database` option. Quit."), "\n")
        exit()
    else:
        answer = input(f"purging <{args.target}>/{target_deployment_path} (y/N)")
        if answer != "y":
            print(du.bred("Aborted."))
            exit()
        c.run(f"rm -r {target_deployment_path}", target_spec="both")

print("\n", "ensure that deployment path exists", "\n")
c.run(f"mkdir -p {target_deployment_path}", target_spec="both")

c.activate_venv(f"~/{venv}/bin/activate")

print("\n", "upload config file", "\n")
c.rsync_upload(config.path, target_deployment_path, target_spec="remote")

c.chdir(target_deployment_path)

print("\n", "upload current application files for deployment", "\n")
# omit irrelevant files (like .git)
# TODO: this should be done more elegantly
filters = \
    f"--exclude='.git/' " \
    f"--exclude='.idea/' " \
    f"--exclude='static_hp/content' " \
    f"--exclude='settings/__pycache__/*' " \
    f"--exclude='{app_name}/__pycache__/*' " \
    f"--exclude='__pycache__/' " \
    f"--exclude='deployment_utils/' " \
    f"--exclude='django_moodpoll.egg-info/' " \
    f"--exclude='db.sqlite3' " \
    ""

c.rsync_upload(project_src_path + "/", target_deployment_path, filters=filters, target_spec="both")

# now rsync instance-specific data (this might overwrite generic data from the project)
# this file should usually not be overwritten
filters = "--exclude='README.md'"
c.rsync_upload(instance_path + "/", target_deployment_path, filters=filters, target_spec="both")

# rsync pelican content
c.rsync_upload(pelican_content_src_dir, pelican_content_dst_dir, filters="", target_spec="remote")

# .............................................................................................

# while this has nothing todo with the database, it serves our purpose to get a fast deployment for the option
if not args.omit_database:
    print("\n", "install dependencies", "\n")
    res = c.run(f'pip show django', target_spec="both", warn=False)
    loc = re.findall("Location:.*", res.stdout)
    if args.target == "local" and len(loc) == 0:
        msg = f"{du.bred('Caution:')} django seems not to be installed on local system.\n" \
              f"This might indicate some problem with pip or the virtualenv not activated.\n"
        print(msg)

        cmd = ["python", "-c", "import sys; print('; '.join(sys.path))"]
        syspath = c.run(cmd, target_spec="local").stdout

        print("This is your current python-path:\n\n", syspath)

        res = input("Continue and install django in that path (N/y)? ")
        if res.lower() != "y":
            print(du.bred("Aborted."))
            exit()

    c.run(f'pip install -r requirements.txt', target_spec="both")

if args.symlink:
    assert args.target == "local"
    app_path = os.path.join(repo_base_dir, app_name)
    c.run(["rm", "-r", os.path.join(target_deployment_path, app_name)], target_spec="local")
    c.run(["ln", "-s", app_path, os.path.join(target_deployment_path, app_name)], target_spec="local")

if not args.initial and not args.omit_backup:

    print("\n", "backup old database", "\n")
    res = c.run('python manage.py savefixtures', target_spec="both")


if not args.omit_database:
    print("\n", "prepare and create new database", "\n")

    # this currently fails (due to no matching directory structure)
    c.run('python manage.py makemigrations', target_spec="both")

    # delete old db
    c.run('rm -f db.sqlite3', target_spec="both")

    # this creates the new database
    c.run('python manage.py migrate', target_spec="both")

    print("\n", "install initial data", "\n")
    c.run(f"python manage.py loaddata {init_fixture_path}", target_spec="both")

if not args.omit_static:
    print("\n", "copy static files to final location", "\n")
    c.run('python manage.py collectstatic --no-input', target_spec="remote")

    if args.target == "remote":
        print("\n", "copy static files to the right place", "\n")
        c.chdir(f"/var/www/virtual/{user}/html")
        c.run('rm -rf static')
        c.run(f'cp -r {static_root_dir} static')

c.chdir(target_deployment_path)

if not args.omit_tests:
    print("\n", "run tests", "\n")
    c.run(f'python manage.py test {app_name}', target_spec="both")

if args.target == "local":
    print("\n", f"now you can go to {target_deployment_path} and run `python manage.py runserver", "\n")
else:
    print("\n", "restart uwsgi service", "\n")
    c.run(f"supervisorctl restart uwsgi", target_spec="remote")

# c.run(f'python manage.py trigger_pelican main', target_spec="both")


print(final_msg)
