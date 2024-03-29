# -*- coding: utf-8 -*-
'''
.. _module_mc_bind:

mc_bind / named/bind functions
============================================
For the documentation on usage, please look :ref:`bind_documentation`.
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils
from copy import deepcopy
import copy
import string
from pprint import pformat
import shutil
import tempfile
import os
from salt.utils.pycrypto import secure_password
from salt.utils.odict import OrderedDict

__name = 'bind'

log = logging.getLogger(__name__)


def generate_tsig(length=128):
    ret = ''
    strings = string.ascii_letters + string.digits
    with open('/dev/urandom', 'r') as fic:
        while len(ret) < length:
            char = fic.read(1)
            if char in strings:
                ret += char
    return ret.encode('base64')


def tsig_for(id_, length=128):
    kid = 'makina-states.services.dns.bind.tsig.{0}'.format(id_)
    local_conf = __salt__['mc_macros.get_local_registry']('bind')
    key = local_conf.get(kid, None)
    if not key:
        local_conf[kid] = generate_tsig(length=length)
        __salt__['mc_macros.update_local_registry']('bind', local_conf)
    return local_conf[kid]


def settings():
    '''
    Named settings

    Without further configuration, this will setup
    a caching name server.
    With a little effort, you can easily turn this server
    in a powerful and flexible nameserver.

    For the documentation on usage, please look :ref:`bind_documentation`.

        pkgs
            pkg to install for a named install
        config
            master config file path
        local_config
            local master config file path
        options_config
            options config file path
        default_zones_config
            default zone config file path
        dnssec
            do we use dnssec (not implemented now)
        named_directory
            var directory
        user
            user for named service (root)
        group
            group for named service (named)
        service_name
            service name
        mode
            configuration files mode ('640')

        views
            List of managed view names
        zones
            List of managed zones names
        serial
            2014030501
        slaves
            default dns server slaves if any
        ttl
            300
        refresh
            300
        retry
            60
        expire
            2419200
        minimum
            299
        rndc_conf
            path to rndc configuration
        rndc_key
            path to rndc key
        servers_config_template
            salt://makina-states/files/etc/bind/named.conf.servers
        key_config_template
            {{settingsnsalt://makina-states/files/etc/bind/named.conf.key
        bind_config_template
            salt://makina-states/files/etc/bind/named.conf
        local_config_template
           salt://makina-states/files/etc/bind/named.conf.local
        options_config_template
           salt://makina-states/files/etc/bind/named.conf.options'
        logging_zones_config_template
           salt://makina-states/files/etc/bind/named.conf.logging
        default_zones_config_template
           salt://makina-states/files/etc/bind/named.conf.default-zones
        zone_template
           salt://makina-states/files/etc/bind/pri_zone.zone
        loglevel

           default
                error
           general
                'error
           database
                error
           config
                error
           security
                error
           resolver
                error
           xfer_in
                nfo
           xfer_out
                info
           notify
                error
           client
                error
           unmatched
                error
           queries
                error
           network
                error
           update
                info
           dispatch
                error
           lame_servers
                error

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        os_defaults = __salt__['grains.filter_by']({
            'Debian': {
                'pkgs': ['bind9',
                         'bind9utils',
                         'bind9-host'],
                'forwarders': [],
                'config_dir': '/etc/bind',
                'bind_config': '/etc/bind/named.conf',
                'acl_config': '/etc/bind/named.conf.acl',
                'views_config': '/etc/bind/named.conf.views',
                'servers_config': (
                    '/etc/bind/named.conf.servers'),
                'logging_config': '/etc/bind/named.conf.logging',
                'local_config': '/etc/bind/named.conf.local',
                'options_config': '/etc/bind/named.conf.options',
                'key_config': '/etc/bind/named.conf.key',
                'default_zones_config': (
                    '/etc/bind/named.conf.default-zones'),
                'cache_directory': '/var/cache/bind',
                'named_directory': '/var/cache/bind/zones',
                'dnssec': True,
                'user': 'root',
                'zuser': 'bind',
                'group': 'bind',
                'service_name': 'bind9',
            },
            'RedHat': {
                'pkgs': ['bind'],
                'config_dir': '/etc',
                'bind_config': '/etc/named.conf',
                'local_config': '/etc/named.conf.local',
                'cache_directory': '/var/named',
                'named_directory': '/var/named/data',
                'user': 'root',
                'group': 'named',
                'service_name': 'named',
            },
        },
            grain='os_family', default='Debian')
        defaults = __salt__['mc_utils.dictupdate'](
            os_defaults, {
                'default_dnses': [],
                'log_dir': '/var/log/named',
                "rndc_conf": "/etc/rndc.conf",
                "rndc_key": "/etc/bind/rndc.key",
                'default_views': OrderedDict([
                    ('internal', {
                        'match_clients': ['local'],
                        'recursion': 'yes',
                        'additional_from_auth': 'yes',
                        'additional_from_cache': 'yes',
                    }),
                    ('net', {
                        'match_clients': [
                            '!local;any'],
                        'recursion': 'no',
                        'additional_from_auth': 'no',
                        'additional_from_cache': 'no',
                    }),
                ]),
                'ipv4': 'any',
                'ipv6': 'any',
                'loglevel': {
                    'default': 'error',
                    'general': 'error',
                    'database': 'error',
                    'config': 'error',
                    'security': 'error',
                    'resolver': 'error',
                    'xfer_in': 'info',
                    'xfer_out': 'info',
                    'notify': 'error',
                    'client': 'error',
                    'unmatched': 'error',
                    'queries': 'error',
                    'network': 'error',
                    'dnssec': 'error',
                    'update': 'info',
                    'dispatch': 'error',
                    'lame_servers': 'error',
                },
                'mode': '640',
                'view_defaults': {
                    'match_clients': ['any'],
                    'recursion': 'no',
                    'additional_from_auth': 'no',
                    'additional_from_cache': 'no',
                },
                'slaves': [],
                'ttl': '330',
                'refresh': '300',
                'retry': '300',
                'expire': '2419200',
                'minimum': '299',
                'bind_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf'
                ),
                'servers_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.servers'
                ),
                'views_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.views'
                ),
                'acl_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.acl'
                ),
                'logging_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.logging'
                ),
                'key_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.key'
                ),
                'local_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.local'
                ),
                'options_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.options'
                ),
                'default_zones_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.default-zones'
                ),
                'rndc_config_template': (
                    'salt://makina-states/files/'
                    'etc/rndc.conf'
                ),
                'zone_template': (
                    'salt://makina-states/files/'
                    'etc/bind/pri_zone.zone'),
                #
                'keys': OrderedDict(),
                'servers': OrderedDict(),
                #
                'views': OrderedDict(),
                #
                'acls': OrderedDict([
                    ('local', {
                        'clients': ['127.0.0.1', '::1',
                                    "192.168.0.0/16", "10.0.0.0/8"],
                        }),
                ]),
                #
                'zones': OrderedDict(),
            }
        )
        defaults['extra_dirs'] = [
            '{0}/zones/master'.format(
                defaults['config_dir']),
            '{0}/zones/slave'.format(
                defaults['config_dir']),
        ]
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.dns.bind', defaults)
        # lighten the data dict for memory purpose
        data['zones'] = [a for a in data['zones']]
        views = [a for a in data['views']]
        data['views'] = []
        for a in views + [b for b in data['default_views']]:
            if a not in data['views']:
                data['views'].append(a)
        for k in data:
            if (
                k.startswith('zones.')
                or k.startswith('views.')
            ):
                del data[k]
        for k in [a for a in data['servers']]:
            adata = data['servers'][k]
            adata.setdefault('keys', [])
        for k in [a for a in data['acls']]:
            adata = data['acls'][k]
            adata.setdefault('clients', 'any')
        for k in [a for a in data['keys']]:
            kdata = data['keys'][k]
            kdata.setdefault('algorithm', 'HMAC-MD5')
            kdata['secret'] = kdata['secret'].strip()
            if 'secret' not in kdata:
                raise ValueError(
                    'no secret for {0}'.format(k))
        for i in ['127.0.0.1', '8.8.8.8', '4.4.4.4']:
            if not i in data['default_dnses']:
                data['default_dnses'].append(i)
        data['default_dnses'] = __salt__['mc_utils.uniquify'](data['default_dnses'])
        return data
    return _settings()


def _generate_rndc():
    data = ''
    return data


def cached_zone_headers():
    '''
    Store a cached but much small memory footprint version
    of all zones data for quickier access to construct
    views in main bind configuration.
    Those keys are enabled:

      - views
      - server_type
      - fqdn
      - masters
      - slaves
      - fpath
      - template
      - source
    '''
    keys = ['views', 'server_type', 'template', 'source',
            'zoneid', 'fqdn', 'fpath']
    zpref = 'makina-states.services.dns.bind.zones'
    @mc_states.utils.lazy_subregistry_get(__salt__, zpref)
    def _settings():
        zones = __salt__['mc_utils.defaults'](zpref, {})
        data = {}
        for zone in zones:
            zdata = get_zone(zone)
            czdata = data.setdefault(zone, {})
            for a in keys:
                czdata[a] = zdata[a]
        return data
    data = _settings()
    for k in ['reg_func_name', 'reg_kind']:
        data.pop(k, '')
    return data


def get_view(view):
    '''Get the mapping describing a bind view

      zones
        light mapping containing zone headers to feed the
        views configuration file.
        See cached_zone_headers
      match_clients
        [any]
      recursion
        no
      additional_from_auth
        no
      additional_from_cache
        no

    '''
    pref = 'makina-states.services.dns.bind.views.{0}'
    _defaults = settings()
    if view in ['net', 'internal']:
        vdefaults = _defaults['default_views'][view]
    else:
        vdefaults = copy.deepcopy(_defaults['view_defaults'])
    zones = vdefaults.setdefault('zones', {})
    for z, data in cached_zone_headers().items():
        if view in data['views']:
            zones[z] = data
    vdata = __salt__['mc_utils.get'](pref.format(view), vdefaults)
    return vdata


def get_zone(zone):
    '''Get the mapping describing a bind zone

      views
          list of views to enable this zone in
      serial
        zone serial
      server_type
          one of master/slave
      ttl
          TTL of soa
      fqdn
          zone FQDN
      soa_ns
          zone main nameserver (ns.{fqdn})
      soa_contact
          soa contact (sysadmin.{fqdn})
      refresh
          refresh(300)
      retry
          retry(60)
      expire
          expire ()
      minimum
          minimum (300)
      notify
          notify
          (true in mastermode and false if slave)
      rrs
          records for the zone in mastermode.
          This list list of records of the zone is in bind
          syntax
      slaves
          list of slaves to allow transfer to in master mode
      masters
          list of master to get zones from in slave mode
      allow_transfer
          list of transfer items
      allow_query
          list of query items
      allow_update
          list of update items
    '''
    pref = 'makina-states.services.dns.bind.zones.{0}'
    defaults = settings()
    zdata = __salt__['mc_utils.defaults'](
        pref.format(zone), {
            'views': [],
            'server_type': 'master',
            'ttl': defaults['ttl'],
            'fqdn': zone,
            'soa_ns': 'ns.{fqdn}.',
            'soa_contact': 'sysadmin.{fqdn}.',
            'serial': '0000000001',
            'refresh': defaults['refresh'],
            'retry': defaults['retry'],
            'expire': defaults['expire'],
            'minimum': defaults['minimum'],
            'notify': None,
            'rrs': None,
            'source': None,
            'allow_query': ['any'],
            'allow_transfer': [],
            'allow_update': [],
            'slaves': defaults['slaves'],
            'masters': []})
    zdata['zoneid'] = zone
    views = zdata['views']
    if zdata['server_type'] not in ['master', 'slave']:
        raise ValueError('invalid {0} type for {1}'.format(
            zdata['server_type', zone]))
    if not views:
        for v in defaults['default_views']:
            if not v in views:
                views.append(v)
    zdata.setdefault('template', True)
    if (
        zdata['server_type'] == 'master'
        and zdata['notify'] is None
    ):
        zdata['notify'] = True
        if zdata['slaves']:
            for slv in zdata['slaves']:
                if not slv in zdata["allow_transfer"]:
                    zdata["allow_transfer"].append(slv)
    if (
        zdata['server_type'] == 'slave'
        and zdata['notify'] is None
    ):
        zdata['notify'] = False
    if not zdata['rrs']:
        zdata['rrs'] = ''
    if zdata['server_type'] == 'master':
        if zdata['source'] is None:
            zdata['source'] = defaults['zone_template']
    if (
        zdata['server_type'] == 'slave'
        and zdata['template']
        and 'masters' not in zdata
    ):
        raise ValueError('no masters for {0}'.format(zone))
    zdata.setdefault('fpath',
                     '{2}/zones/{0}/{1}.conf'.format(
                         zdata['server_type'],
                         zdata['fqdn'],
                         defaults['config_dir']))
    zdata = __salt__['mc_utils.format_resolve'](zdata)
    return zdata


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
