#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
'''

.. _module_mc_cloud_lxc:

mc_cloud_lxc / lxc registry for compute nodes
===============================================

'''

# Import python libs
import logging
import mc_states.utils
from pprint import pformat
import os
import random
import socket
import copy


from mc_states import saltapi
from salt.utils.odict import OrderedDict
from salt.utils.pycrypto import secure_password

_errmsg = saltapi._errmsg
__name = 'mc_cloud_lxc'

log = logging.getLogger(__name__)


def gen_mac():
    return ':'.join(map(lambda x: "%02x" % x, [0x00, 0x16, 0x3E,
                                               random.randint(0x00, 0x7F),
                                               random.randint(0x00, 0xFF),
                                               random.randint(0x00, 0xFF)]))

def is_lxc():
    """
    in case of a container, we have the container name in cgroups
    else, it is equal to /

    in lxc:
        ['11:name=systemd:/user/1000.user/1.session',
        '10:hugetlb:/thisname',
        '9:perf_event:/thisname',
        '8:blkio:/thisname',
        '7:freezer:/thisname',
        '6:devices:/thisname',
        '5:memory:/thisname',
        '4:cpuacct:/thisname',
        '3:cpu:/thisname',
        '2:cpuset:/thisname']

    in host:
        ['11:name=systemd:/',
        '10:hugetlb:/',
        '9:perf_event:/',
        '8:blkio:/',
        '7:freezer:/',
        '6:devices:/',
        '5:memory:/',
        '4:cpuacct:/',
        '3:cpu:/',
        '2:cpuset:/']
    """

    try:
        cgroups = open('/proc/1/cgroup').read().splitlines()
        lxc = not '/' == [a.split(':')[-1]
                          for a in cgroups if ':cpu:' in a][-1]
    except Exception:
        lxc = False
    return lxc


def settings():
    '''Lxc registry

    makina-states.services.cloud.lxc
        The settings of lxc containers that are meaningful on the
        cloud controller

    cloud defaults (makina-states.services.cloud.lxc)
        defaults settings to provision lxc containers
        Those are all redefinable at each container level

        ssh_gateway
            ssh gateway info
        ssh_gateway_port
            ssh gateway info
        ssh_gateway_user
            ssh gateway info
        ssh_gateway_key
            ssh gateway info
        size
            default filesystem size for container on lvm
            None
        default_container
            default image

        gateway
            '10.5.0.1'
        master
            master to uplink the container to
            None
        master_port
            '4506'
        image
            LXC template to use
            'ubuntu'
        bootsalt_branch
            branch of makina-states to use (prod in prod, dev in dev by default (default_env grain))
        network
            '10.5.0.0'
        netmask
            '16'
        netmask_full
            '255.255.0.0'
        autostart
            lxc is autostarted
        mode
            (salt (default) or mastersalt)
        profile
            default size profile to use (medium) (apply only to lvm)
        profile_type
            default profile type to use (lvm)

                lvm
                    lvm backend from default container
                lvm-scratch
                    lvm backend from default lxc template
                dir
                    dir backend from default container
                dir-scratch
                    dir backend from default lxc template

        bridge
            we install via states a bridge in 10.5/16 lxcbr1)
            'lxcbr1'
        sudo
            True
        use_bridge
            True
        backing
            (lvm, overlayfs, dir, brtfs) 'lvm'
        users
            ['root', 'sysadmin']
        ssh_username
            'ubuntu'
        vgname
            'data'
        lvname
            'data'
        lxc_conf
            []
        lxc_conf_unset'
            []
    vm
        Mapping of containers defintions classified by host
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        nt_registry = __salt__['mc_nodetypes.registry']()
        cloudSettings = __salt__['mc_cloud.settings']()
        imgSettings = __salt__['mc_cloud_images.settings']()
        default_container = [a for a in imgSettings['lxc']][0]
        default_vm = OrderedDict()
        # reactivate to provision
        # when you do maintenance
        # default_container:
        maintenance = False
        if maintenance:
            default_vm[grains['id']] = {
                'name': default_container,
                'profile_type': 'dir-scratch',
                'ip': '0.0.0.0',  # set later
                'mode': 'mastersalt',
                'image': 'ubuntu',
                'password': 'ubuntu',
            }
        # no lvm on devhost
        # nor cron sync
        dptype = 'lvm'
        backing = 'lvm'
        if nt_registry['is']['devhost']:
            dptype = 'dir'
            backing = 'dir'
        lxcSettings = __salt__['mc_utils.defaults'](
            'makina-states.cloud.lxc', {
                'dnsservers': ['8.8.8.8', '4.4.4.4'],
                'defaults': {
                    'default_container': default_container,
                    'autostart': True,
                    'size': None,  # via profile
                    'profile': 'medium',
                    'profile_type': dptype,
                    'gateway': '10.5.0.1',
                    'mode': cloudSettings['mode'],
                    'ssh_gateway': cloudSettings['ssh_gateway'],
                    'ssh_gateway_password': cloudSettings['ssh_gateway_password'],
                    'ssh_gateway_user': cloudSettings['ssh_gateway_user'],
                    'ssh_gateway_key': cloudSettings['ssh_gateway_key'],
                    'ssh_gateway_port': cloudSettings['ssh_gateway_port'],
                    'master': cloudSettings['master'],
                    'master_port': cloudSettings['master_port'],
                    'image': 'ubuntu',
                    'network': '10.5.0.0',
                    'netmask': '16',
                    'bootsalt_branch': cloudSettings['bootsalt_branch'],
                    'netmask_full': '255.255.0.0',
                    'bridge': 'lxcbr1',
                    'sudo': True,
                    'use_bridge': True,
                    'backing': backing,
                    'users': ['root', 'sysadmin'],
                    'ssh_username': 'ubuntu',
                    'vgname': 'lxc',
                    'lvname': None,
                    'lxc_conf': [],
                    'lxc_conf_unset': [],
                },
                'vms': default_vm,
                'lxc_cloud_profiles': {
                    'xxxtrem': {'size': '2000g', },
                    'xxtrem': {'size': '1000g', },
                    'xtrem': {'size': '500g', },
                    'xxxlarge': {'size': '100g', },
                    'xxlarge': {'size': '50g', },
                    'large': {'size': '20g', },
                    'medium': {'size': '10g', },
                    'small': {'size': '5g', },
                    'xsmall': {'size': '3g', },
                    'xxsmall': {'size': '1g', },
                    'xxxsmall': {'size': '500m', },
                }
            }
        )
        if maintenance and (
            '0.0.0.0' ==
            lxcSettings['vms'][
                grains['id']][default_container]['ip']
        ):
            lxcSettings['vms'][
                grains['id']][default_container]['ip'] = (
                '.'.join(
                    lxcSettings['defaults']['network'].split(
                        '.')[:3] + ['2']))
        for target in [t for t in lxcSettings['vms']]:
            master = lxcSettings['defaults']['master']
            # if it is not a distant minion, use private gateway ip
            if __grains__['id'] == target:
                master = lxcSettings['defaults']['gateway']
            # filter dicts and overiddes
            for container in lxcSettings['vms'][target]:
                lxc_data = lxcSettings['vms'][target][container]
                lxc_data.setdefault('master', master)
                lxc_data.setdefault('ssh_gateway', target)
                lxc_data['mac'] = find_mac_for_container(
                    target, container, lxc_data)
                for i in ['ip']:
                    if not i in lxc_data:
                        raise Exception(
                            'Missing data {1}\n:{0}'.format(i, lxc_data))
                # shortcut name for profiles
                # small -> ms-target-small
                profile_type = lxc_data.get(
                    'profile_type',
                    lxcSettings['defaults']['profile_type'])
                profile = lxc_data.get('profile',
                                       lxcSettings['defaults']['profile'])
                if (
                    profile in lxcSettings['lxc_cloud_profiles']
                    and 'profile' in lxc_data
                ):
                    del lxc_data['profile']
                if 'dir' in profile_type or 'scratch' in profile_type:
                    sprofile = ''
                    lxc_data['backing'] = 'dir'
                else:
                    sprofile = '-{0}'.format(profile)
                lxc_data.setdefault(
                    'profile', __salt__['mc_cloud_controller.gen_id'](
                        'ms-{0}{1}-{2}'.format(
                            target, sprofile, profile_type)))
                lxc_data.setdefault('name', container)
                lxc_data.setdefault('mode', lxcSettings['defaults']['mode'])
                lxc_data.setdefault('size', None)
                lxc_data.setdefault('from_container', None)
                lxc_data.setdefault('snapshot', None)
                if 'mastersalt' in lxc_data.get('mode', 'salt'):
                    default_args = cloudSettings['bootsalt_mastersalt_args']
                else:
                    default_args = cloudSettings['bootsalt_args']
                lxc_data['script_args'] = lxc_data.get('script_args',
                                                       default_args)
                branch = lxc_data.get('bootsalt_branch',
                                      cloudSettings['bootsalt_branch'])
                if (
                    not '-b' in lxc_data['script_args']
                    or not '--branch' in lxc_data['script_args']
                ):
                    lxc_data['script_args'] += ' -b {0}'.format(branch)

                if not 'scratch' in profile_type:
                    lxc_data.setdefault(
                        'from_container',
                        lxcSettings['defaults']['default_container'])
                lxc_data = saltapi.get_gateway(
                    lxc_data, lxcSettings)
                for i in ["from_container", 'bootsalt_branch',
                          "master", "master_port", "autostart",
                          'size', 'image', 'bridge', 'netmask', 'gateway',
                          'dnsservers', 'backing', 'vgname', 'lvname',
                          "gateway",
                          'vgname', 'ssh_username', 'users', 'sudo',
                          'lxc_conf_unset', 'lxc_conf']:
                    lxc_data.setdefault(
                        i,
                        lxcSettings['defaults'].get(i,
                                                    lxcSettings.get(i, None)))
                if 'dir' in profile_type:
                    for k in ['lvname', 'vgname', 'size']:
                        if k in lxc_data:
                            del lxc_data[k]
        return lxcSettings
    return _settings()


def find_mac_for_container(target, container, lxc_data=None):
    '''Generate and assign a mac addess to a specific
    container on a speific host'''
    if not lxc_data:
        lxc_data = {}
    gid = 'makina-states.services.cloud.lxc.vmsettings.{1}.{1}.mac'.format(
        target, container)
    mac = lxc_data.get('mac', __salt__['mc_utils.get'](gid, None))
    if not mac:
        __salt__['grains.setval'](gid, gen_mac())
        __salt__['saltutil.sync_grains']()
        mac = __salt__['mc_utils.get'](gid)
        if not mac:
            raise Exception(
                'Error while setting grainmac for {0}/{1}'.format(target,
                                                                  container))
    return mac


def find_password_for_container(target,
                                container,
                                lxc_data=None,
                                pwlen=32):
    '''Return the container password after creating it 
    the first time
    THIS IS NOT IMPLEMENTED YET
    '''
    raise Exception('Not implemented')
    if not lxc_data:
        lxc_data = {}
    password = lxc_data.get('password', None)
    gid = ('makina-states.services.cloud.'
           'lxc.vmsettings.'
           '{1}.{1}.password').format(target, container)
    if not password:
        __salt__['grains.setval'](gid, secure_password(pwlen))
        __salt__['saltuitil.sync_grains']()
        password = __salt__['mc_utils.get'](gid)
        if not password:
            raise Exception(
                'Error while setting password grain for {0}/{1}'.format(
                    target, container))
    return password


def find_ip_for_container(target, container, lxc_data=None):
    '''Search for:

        - an ip in lxc.conf
        - an ip already allocated
        - an random available ip in the range

    THIS IS NOT IMPLEMENTED YET
    '''
    raise Exception('Not implemented')
    if not lxc_data:
        lxc_data = {}
    ip4 = lxc_data.get('ip4', None)
    gid = 'makina-states.services.virt.lxc.vm.{0}.{1}.ip4'.format(
        target, container)
    if not ip4:
        __salt__['grains.setval'](gid, gen_ip4())
        __salt__['saltuitil.sync_grains']()
        ip4 = __salt__['mc_utils.get'](gid)
        if not ip4:
            raise Exception(
                'Error while setting grainip4 for {0}/{1}'.format(target,
                                                              container))
    return ip4


def dump():
    return mc_states.utils.dump(__salt__,__name)



# vim:set et sts=4 ts=4 tw=80:
