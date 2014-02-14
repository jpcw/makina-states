# -*- coding: utf-8 -*-
'''
mc_bootstraps / bootstraps related registry
============================================

'''

# Import salt libs
import mc_states.utils

__name = 'bootstraps'


def metadata():
    '''metadata registry for bootstraps'''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata']('bootstraps')
    return _metadata()


def settings():
    '''settings registry for bootstraps'''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        resolver = saltmods['mc_utils.format_resolve']
        metadata = saltmods['mc_{0}.metadata'.format(__name)]()
        return locals()
    return _settings()


def registry():
    '''registry registry for bootstraps'''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _registry():
        settings_reg = __salt__['mc_{0}.settings'.format(__name)]()
        return __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={})
    return _registry()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
