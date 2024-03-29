# -*- coding: utf-8 -*-
'''
.. _module_mc_project:

mc_project / project settings regitry switcher and common functions
=====================================================================

'''

from mc_states.project import LAST_PROJECT_API_VERSION
from mc_states import api


APIS = {
    'report': {
        '2': 'mc_project_2.report',
    },
    'deploy': {
        '2': 'mc_project_2.deploy',
    },
    'init_project': {
        '2': 'mc_project_2.init_project',
    },
    'archive': {
        '2': 'mc_project_2.archive',
    },
    'rotate_archives': {
        '2': 'mc_project_2.rotate_archives',
    },
    'link': {
        '2': 'mc_project_2.link',
    },
    'unlink': {
        '2': 'mc_project_2.unlink',
    },
    'release_sync': {
        '2': 'mc_project_2.release_sync',
    },
    'install': {
        '2': 'mc_project_2.install',
    },
    'run_task': {
        '2': 'mc_project_2.run_task',
    },
    'fixperms': {
        '2': 'mc_project_2.fixperms',
    },
    'notify': {
        '2': 'mc_project_2.notify',
    },
    'rollback': {
        '2': 'mc_project_2.rollback',
    },
    'get_configuration': {
        '1': 'mc_project_1.get_configuration',
        '2': 'mc_project_2.get_configuration',
    },
    'set_configuration': {
        '2': 'mc_project_2.set_configuration',
    },
}


def _api_switcher(module, *args, **kwargs):
    '''Get the right module:

            - from explicitly given api
            - from local project configuration
            - fallback on last API
    '''
    try:
        api_ver = kwargs.pop('api_ver')
    except KeyError:
        if args:
            api_ver = __salt__['mc_utils.get'](
                'makina-projects.{0}.api_version'.format(
                    args[0]),
                LAST_PROJECT_API_VERSION)
        else:
            api_ver = LAST_PROJECT_API_VERSION
    mod = APIS[module]["{0}".format(api_ver)]
    return __salt__[mod](*args, **kwargs)


def get_configuration(name, *args, **kwargs):
    return _api_switcher('get_configuration', name, *args, **kwargs)


def set_configuration(name, *args, **kwargs):
    return _api_switcher('set_configuration', name, *args, **kwargs)


def init_project(name, *args, **kwargs):
    return _api_switcher('init_project', name, *args, **kwargs)


def report(*args, **kwargs):
    return _api_switcher('report')


def deploy(name, *args, **kwargs):
    return _api_switcher('deploy', name, *args, **kwargs)


def archive(name, *args, **kwargs):
    return _api_switcher('archive', name, *args, **kwargs)


def release_sync(name, *args, **kwargs):
    return _api_switcher('release_sync', name, *args, **kwargs)


def fixperms(name, *args, **kwargs):
    return _api_switcher('fixperms', name, *args, **kwargs)


def rotate_archives(name, *args, **kwargs):
    return _api_switcher('rotate_archives', name, *args, **kwargs)


def unlink(name, *args, **kwargs):
    return _api_switcher('unlink', name, *args, **kwargs)


def install(name, *args, **kwargs):
    return _api_switcher('install', name, *args, **kwargs)


def link(name, *args, **kwargs):
    return _api_switcher('link', name, *args, **kwargs)


def run_task(name, *args, **kwargs):
    return _api_switcher('run_task', name, *args, **kwargs)


def doc_root(doc_root=None,
             domain=None,
             project_root=None,
             project=None,
             relative_document_root='www'):
    if not doc_root:
        if not domain and not project:
            raise Exception('Need at least one of domain or project')
        if not project:
            project = gen_id(domain)
        if not project_root:
            project_root = '{0}/{1}/project'.format(
                __salt__['mc.locations.settings']()['projects_dir'], project)
        doc_root = '{0}/{1}'.format(project_root,
                                    relative_document_root)
    return doc_root


def uniquify(seq):
    return api.uniquify(seq)


def gen_id(id):
    return id.replace('.', '-')


def server_aliases(value):
    if not isinstance(value, list):
        value = value.split()
    return value


def get_common_vars(*args, **kwargs):
    '''Retro compat, wrapper to get_configuration'''
    return __salt__['mc_project_1.get_configuration'](*args, **kwargs)
#
