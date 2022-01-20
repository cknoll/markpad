import time
import os
import re
import deploymentutils as du
from os.path import join as pjoin


from ipydex import IPS, activate_ips_on_exception

# simplify debugging
activate_ips_on_exception()


"""
This script serves to deploy and maintain the django application with which it is delivered.
It is largely based on this tutorial: <https://lab.uberspace.de/guide_django.html>.
"""


# call this before running the script:
# eval $(ssh-agent); ssh-add -t 10m


# this file must be changed according to your uberspace accound details (machine name and user name)
cfg = du.get_nearest_config("config-production.ini")


remote = cfg("remote_hostname")
user = cfg("user")

app_name = "mainapp"  # this is the name of the django app (not the project)
project_name = cfg("PROJECT_NAME")

# this is needed to distinguish different django instances on the same uberspace account
port = cfg("port")
django_url_prefix = cfg("django_url_prefix")
static_url_prefix = cfg("static_url_prefix")


asset_dir = pjoin(du.get_dir_of_this_file(), "files")  # contains the templates
temp_workdir = pjoin(du.get_dir_of_this_file(), "tmp_workdir")  # this will be deleted/overwritten

# -------------------------- Begin Optional Config section -------------------------
# if you know what you are doing you can adapt these settings to your needs

# this is the root dir of the project (where setup.py lies)
# if you maintain more than one instance (and deploy.py lives outside the project dir, this has to change)
project_src_path = os.path.dirname(du.get_dir_of_this_file())


# name of the directory for the virtual environment:
venv = cfg("venv")
venv_path = f"/home/{user}/{venv}"

# because uberspace offers many python versions:
pipc = cfg("pip_command")
python_version = cfg("python_version")

du.argparser.add_argument(
    "--dbg", action="store_true", help="start interactive shell for debugging. Then exit"
)

du.argparser.add_argument(
    "--omit_requirements",
    action="store_true",
    help="do not install requirements (allows to speed up deployment)",
)

du.argparser.add_argument("--omit_database", action="store_true", help="omit database handling")

du.argparser.add_argument(
    "--omit_static", action="store_true", help="omit handling of static files"
)

du.argparser.add_argument("--omit-tests", action="store_true", help="omit test execution")

args = du.parse_args()

final_msg = f"Deployment script {du.bgreen('done')}."

if not args.target == "remote":
    raise NotImplementedError

# this is where the code will live after deployment
target_deployment_path = cfg("deployment_path")
static_root_dir = f"{target_deployment_path}/collected_static"
debug_mode = False

# print a warning for data destruction
du.warn_user(
    cfg("PROJECT_NAME"),
    args.target,
    args.unsafe,
    deployment_path=target_deployment_path,
    user=user,
    host=remote,
)

# ensure clean workdir
os.system(f"rm -rf {temp_workdir}")
os.makedirs(temp_workdir)

c = du.StateConnection(remote, user=user, target=args.target)


def create_and_setup_venv(c):

    c.run(f"{pipc} install --user virtualenv")

    print("create and activate a virtual environment inside $HOME")
    c.chdir("~")

    c.run(f"rm -rf {venv}")
    c.run(f"virtualenv -p {python_version} {venv}")

    c.activate_venv(f"~/{venv}/bin/activate")

    c.run(f"pip install --upgrade pip")
    c.run(f"pip install --upgrade setuptools")

    print("\n", "install uwsgi", "\n")
    c.run(f"pip install uwsgi")

    # ensure that the same version of deploymentutils like on the controller-pc is also in the server
    c.deploy_this_package()


def render_and_upload_config_files(c):

    c.activate_venv(f"~/{venv}/bin/activate")

    # generate the general uwsgi ini-file
    tmpl_dir = os.path.join("uberspace", "etc", "services.d")
    tmpl_name = "template_PROJECT_NAME_uwsgi.ini"
    target_name = "PROJECT_NAME_uwsgi.ini".replace("PROJECT_NAME", project_name)
    du.render_template(
        tmpl_path=pjoin(asset_dir, tmpl_dir, tmpl_name),
        target_path=pjoin(temp_workdir, tmpl_dir, target_name),
        context=dict(venv_abs_bin_path=f"{venv_path}/bin/", project_name=project_name),
    )

    # generate config file for django uwsgi-app
    tmpl_dir = pjoin("uberspace", "uwsgi", "apps-enabled")
    tmpl_name = "template_PROJECT_NAME.ini"
    target_name = "PROJECT_NAME.ini".replace("PROJECT_NAME", project_name)
    du.render_template(
        tmpl_path=pjoin(asset_dir, tmpl_dir, tmpl_name),
        target_path=pjoin(temp_workdir, tmpl_dir, target_name),
        context=dict(
            venv_dir=f"{venv_path}", deployment_path=target_deployment_path, port=port, user=user
        ),
    )

    #
    # ## upload config files to remote $HOME ##
    #
    srcpath1 = os.path.join(temp_workdir, "uberspace")
    filters = "--exclude='**/README.md' --exclude='**/template_*'"  # not necessary but harmless
    c.rsync_upload(srcpath1 + "/", "~", filters=filters, target_spec="remote")


def update_supervisorctl(c):

    c.activate_venv(f"~/{venv}/bin/activate")

    c.run("supervisorctl reread", target_spec="remote")
    c.run("supervisorctl update", target_spec="remote")
    print("waiting 10s for uwsgi to start")
    time.sleep(10)

    res1 = c.run("supervisorctl status", target_spec="remote")

    assert "uwsgi" in res1.stdout
    assert "RUNNING" in res1.stdout


def set_web_backend(c):
    c.activate_venv(f"~/{venv}/bin/activate")

    c.run(
        f"uberspace web backend set {django_url_prefix} --http --port {port}", target_spec="remote"
    )

    # note 1: the static files which are used by django are served under '{static_url_prefix}'/
    # (not {django_url_prefix}}{static_url_prefix})
    # they are served by apache from ~/html{static_url_prefix}, e.g. ~/html/markpad1-static

    c.run(f"uberspace web backend set {static_url_prefix} --apache", target_spec="remote")


def upload_files(c):
    print("\n", "ensure that deployment path exists", "\n")
    c.run(f"mkdir -p {target_deployment_path}", target_spec="both")

    c.activate_venv(f"~/{venv}/bin/activate")

    print("\n", "upload config file", "\n")
    c.rsync_upload(cfg.path, target_deployment_path, target_spec="remote")

    c.chdir(target_deployment_path)

    print("\n", "upload current application files for deployment", "\n")
    # omit irrelevant files (like .git)
    # TODO: this should be done more elegantly
    filters = f"--exclude='.git/' " f"--exclude='.idea/' " f"--exclude='db.sqlite3' " ""

    c.rsync_upload(
        project_src_path + "/", target_deployment_path, filters=filters, target_spec="both"
    )


def purge_deployment_dir(c):
    if not args.omit_backup:
        print(
            "\n",
            du.bred("  The `--purge` option explicitly requires the `--omit-backup` option. Quit."),
            "\n",
        )
        exit()
    else:
        answer = input(f"purging <{args.target}>/{target_deployment_path} (y/N)")
        if answer != "y":
            print(du.bred("Aborted."))
            exit()
        c.run(f"rm -r {target_deployment_path}", target_spec="both")


def install_app(c):
    c.activate_venv(f"~/{venv}/bin/activate")

    c.chdir(target_deployment_path)
    c.run(f"pip install -r requirements.txt", target_spec="both")


def initialize_db(c):

    c.chdir(target_deployment_path)
    c.run("python manage.py makemigrations", target_spec="both")

    # This deletes all data (OK for this app but probably not OK for others) -> backup db before

    # print("\n", "backup old database", "\n")
    # res = c.run('python manage.py savefixtures', target_spec="both")

    # delete old db
    c.run("rm -f db.sqlite3", target_spec="both")

    # this creates the new database
    c.run("python manage.py migrate", target_spec="both")

    # print("\n", "install initial data", "\n")
    # c.run(f"python manage.py loaddata {init_fixture_path}", target_spec="both")


def generate_static_files(c):

    c.chdir(target_deployment_path)

    c.run("python manage.py collectstatic --no-input", target_spec="remote")

    print("\n", "copy static files to the right place", "\n")
    c.chdir(f"/var/www/virtual/{user}/html")
    c.run(f"rm -rf ./{static_url_prefix}")
    c.run(f"cp -r {static_root_dir} ./{static_url_prefix}")

    c.chdir(target_deployment_path)


def run_tests(c):
    c.chdir(target_deployment_path)
    print("\n", "run tests", "\n")
    c.run(f"python manage.py test {app_name}", target_spec="both")


if args.dbg:
    c.activate_venv(f"{venv_path}/bin/activate")

    # c.deploy_local_package("/home/ck/projekte/rst_python/ipydex/repo")

    IPS()
    exit()

if args.initial:

    # create_and_setup_venv(c)
    render_and_upload_config_files(c)
    update_supervisorctl(c)
    set_web_backend(c)


upload_files(c)

if not args.omit_requirements:
    install_app(c)

if not args.omit_database:
    initialize_db(c)

if not args.omit_static:
    generate_static_files(c)

if not args.omit_tests:
    run_tests(c)

print("\n", "restart uwsgi service", "\n")
c.run(f"supervisorctl restart all", target_spec="remote")


print(final_msg)
