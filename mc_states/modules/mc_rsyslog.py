# -*- coding: utf-8 -*-
'''
.. _module_mc_rsyslog:

mc_rsyslog / rsyslog functions
==================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import os
import mc_states.utils

__name = 'rsyslog'

log = logging.getLogger(__name__)


def settings():
    '''
    rsyslog settings

    spool
        spool directory
    user
        syslog user
    group
        syslog group
    admin_group
        admin group
    listen_addr
        listen address

            - 0.0.0.0 on baremetal
            - 127.0.0.1 on vms

        Yes syslog is opened to world on baremetal,
        but we filter it using the restriction feature
        of our shorewall installation, see :ref:`module_mc_shorewall`,
        so please install also shorewall ! By default on baremetal
        it will accept only localhost traffic.

    udp_port
        udp port (514)

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        nt_reg = __salt__['mc_nodetypes.registry']()
        locs = __salt__['mc_locations.settings']()
        listen_addr = '0.0.0.0'
        if nt_reg['is']['vm']:
            listen_addr = '127.0.0.1'
        xconsole = True
        kernel_log = True
        haproxy = False
        if (
            __salt__['mc_services.registry']()['has']['proxy.haproxy']
            or os.path.exists('/etc/haproxy')
        ):
            haproxy = True
        if __salt__['mc_lxc.is_lxc']():
            kernel_log = False
            xconsole = False
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.log.rsyslog', {
                'spool': '/var/spool/rsyslog',
                'haproxy': haproxy,
                'user': 'syslog',
                'group': 'syslog',
                'admin_group': 'adm',
                'listen_addr': listen_addr,
                'kernel_log': kernel_log,
                'xconsole': xconsole,
                'udp_port': '514',
            }
        )
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
