#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_rvm:

mc_rvm / rvm registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_rvm

'''
# Import python libs
import logging
import mc_states.utils

__name = 'rvm'

log = logging.getLogger(__name__)
RVM_URL = (
    'https://raw.github.com/wayneeseguin/rvm/master/binscripts/rvm-installer')


def settings():
    '''
    rvm registry

    rvm_url
        rvm download url
    rubies
        Activated rubies
    rvm_user
        RVM user
    rvm_group
        RVM group

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        grains = __grains__
        # users data
         # RVM
        data = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.rvm', {
                'url': RVM_URL,
                'rubies': ['1.9.3'],
                'user': 'rvm',
                'group': 'rvm'
            })
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# vim:set et sts=4 ts=4 tw=80:
