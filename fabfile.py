# Timego fabfile

from fabric.api import *
from fabric.operations import *
from fabric.utils import *
from fabric.contrib.files import *
from fabric.colors import green, yellow, red

"""
Base configuration
"""
env.disable_known_hosts = True
env.project_name = 'timego'
env.site_media_prefix = "static"
env.path = '/home/timego/sites/%(project_name)s' % env
env.log_path = '/home/timego/logs/%(project_name)s' % env
env.env_path = '%(path)s/env' % env
env.src_path = '%(path)s/src' % env
env.repo_path = '%(path)s/repository' % env
env.static_path = '%(path)s/repository/timego/static' % env
env.media_path = '%(path)s/repository/timego/media' % env
env.apache_path = '/etc/apache2'
env.apache_config_path = '%(apache_path)s/sites-enabled/timego' % env
env.python = 'python2.6'
env.repository_url = "git@github.com:Timego/timego.git"
#env.django_site_id = "4d5cf5d173ae55149600001f"
env.site_packages = "%(env_path)s/lib/%(python)s/site-packages" % env


"""
Environments
"""
def production():
    """
    Selects production environment.
    """
    pass

def staging():
    """
    Selects staging environment.
    """
    env.settings = 'staging'
    env.hosts = ['qcl.csie.org:2222']
    env.user = 'timego'
    env.generic = False

def generic(host_name):
    """
    Selects generic environment (arbitrary host)
    """
    env.settings = 'generic'
    env.hosts = [host_name,]
    env.user = 'timego'
    env.generic = True # NOT staging / production deployment


"""
Branches
"""
def stable():
    """
    Selects stable branch.
    """
    env.branch = 'stable'

def master():
    """
    Selects development branch.
    """
    env.branch = 'master'

def branch(branch_name):
    """
    Selects any an arbitrary branch.
    """
    env.branch = branch_name

"""
Commands - setup
"""
def setup():
    """
    Sets up a remote deployment environment.
    
    Does NOT perform the functions of deploy().
    """
    require('generic', 'settings', provided_by=[production, staging, generic])
    require('branch', provided_by=[stable, master, branch])

    if env.generic:
        print green("Performing a generic setup on: %s" % env.hosts[0])
    else:
        print green("Performing a staging/production setup on: %s" % env.hosts[0])

    setup_directories()
    setup_virtualenv()
    clone_repo()
    checkout_latest()
    fix_perms()
    install_django_nonrel()
    install_requirements()

    #if env.generic:
    #    write_conf_generic()

    #install_webserver_conf()
    #collect_static()
    #rebuild_solr_index()
    #reboot()

def setup_directories():
    """
    Creates directories necessary for deployment.
    """
    print yellow("Creating project directories...")

    run('mkdir -p %(path)s' % env)
    run('mkdir -p %(env_path)s' % env)
    run('mkdir -p %(src_path)s' % env)
    run ('mkdir -p %(log_path)s;' % env)
    sudo('chgrp -R www-data %(log_path)s; chmod -R g+w %(log_path)s;' % env)
    run('ln -s %(log_path)s %(path)s/logs' % env)

def setup_virtualenv():
    """
    Sets up a fresh virtualenv and installs pip.
    """
    print yellow("Setting up a fresh virtual environment...")

    run('virtualenv -p %(python)s --no-site-packages %(env_path)s;' % env)
    with prefix('source %(env_path)s/bin/activate' % env):
        run('easy_install -U setuptools; easy_install pip;' % env)

def clone_repo():
    """
    Do initial clone of the git repository.
    """
    print yellow("Cloning git repo...")

    run('git clone -q %(repository_url)s %(repo_path)s' % env)
    run('mkdir %(repo_path)s/timego/media' % env)
    run('mkdir %(repo_path)s/timego/static' % env)

def install_requirements():
    """
    Install the required packages using pip.
    """
    print yellow("Installing pip requirements...")

    with prefix('source %(env_path)s/bin/activate' % env):
        run('pip install -E %(env_path)s -r %(repo_path)s/requirements.txt' % env)

def checkout_latest():
    """
    Pull the latest code on the specified branch.  Overwrites any local
    configuration changes.
    """
    print yellow("Pulling latest source...")

    with prefix('cd %(repo_path)s' % env):
        sudo('chown -R %(user)s %(path)s' % env)
        run('git reset --hard HEAD')
        run('git checkout %(branch)s' % env)
        run('git pull origin %(branch)s' % env)

def fix_perms():
    """
    Gives www-data user write permissions to media directory
    """
    sudo('chown -R www-data %(repo_path)s/%(project_name)s/media' % env)

