# -*- coding: utf-8 -*-
'''

.. _module_mc_shorewall:

mc_shorewall / shorewall functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import socket
import logging
from distutils.version import LooseVersion
import mc_states.utils
from salt.utils.odict import OrderedDict

__name = 'shorewall'

log = logging.getLogger(__name__)


def guess_shorewall_ver():
    ver = __salt__['cmd.run']('shorewall version')
    for i in ['3' '4', '5']:
        if i in ver:
            return ver
    if __grains__['os'] in ['Debian']:
        if __grains__['osrelease'][0] < '6':
            osver = 'old_deb'
        else:
            osver = 'deb'
    else:
        osver = 'ubuntu'
    if __grains__.get('lsb_distrib_codename') in ['precise']:
        osver = 'precise'
    ver = {
        'old_deb': '4.0.15',
        'deb': '4.5.0',
        'precise': '4.4.26',
        'ubuntu': '4.5.17',
    }.get(osver, '4.5.17')
    return ver


def get_macro(name, action):
    if guess_shorewall_ver() < '4.5.10':
        fmt = '{name}/{action}'
    else:
        fmt = '{name}({action})'
    return fmt.format(name=name, action=action)


def append_rules_for_zones(default_rules, rules, zones=None):
    if not isinstance(rules, list):
        rules = [rules]
    if not zones:
        zones = ['all']
    for rule in rules:
        if 'comment' in rule:
            default_rules.append(rule)
        else:
            for zone in zones:
                crule = rule.copy()
                crule['dest'] = zone
                default_rules.append(crule)


def prefered_ips(bclients):
    clients = []
    for client in bclients:
        try:
            clients.append(socket.gethostbyname(client))
        except Exception:
            clients.append(client)
    return clients


def settings():
    '''
    shorewall settings

    makina-states.services.shorewall.enabled: activate shorewall

    It will also assemble pillar slugs to make powerfull firewalls
    by parsing all **\*-makina-shorewall** pillar entries to load the special shorewall structure:

    All entries are merged in the lexicograpĥical order

    makina-states.services.firewall.shorewall:
        interfaces
            TBD
        rules
            TBD
        params
            TBD
        policies
            TBD
        zones
            TBD
        masqs
            TBD
        proxyarp
            TBD
        nat
            TBD

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        protos = ['tcp', 'udp']
        grains = __grains__
        pillar = __pillar__
        data_net = __salt__['mc_network.default_net']()
        default_netmask = data_net['default_netmask']
        gifaces = data_net['gifaces']
        default_if = data_net['default_if']
        default_route = data_net['default_route']
        default_net = data_net['default_net']
        services_registry = __salt__['mc_services.registry']()
        controllers_registry = __salt__['mc_controllers.registry']()
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        locs = __salt__['mc_locations.settings']()
        providers = __salt__['mc_provider.settings']()
        have_rpn = providers['have_rpn']
        #if ((grains['os'] not in ['Debian'])
        #   and (grains.get('lsb_distrib_codename') not in ['precise'])):
        ulogd = False
        if nodetypes_registry['is']['lxccontainer']:
            ulogd = True

        sw_ver = guess_shorewall_ver()
        shwIfformat = '?FORMAT 2'
        if LooseVersion('4.5.10') >= LooseVersion(sw_ver):
            shwIfformat = '?FORMAT 2'
        if LooseVersion('4.5.10') > LooseVersion(sw_ver) > LooseVersion('4.1'):
            shwIfformat = 'FORMAT 2'
        elif LooseVersion(sw_ver) <= LooseVersion('4.1'):
            shwIfformat = '#?{0}'.format(shwIfformat)
        permissive_mode = False
        if nodetypes_registry['is']['lxccontainer']:
            # be permissive on the firewall side only if we are
            # routing via the host only network and going
            # outside througth NAT
            # IOW
            # if we have multiple interfaces and the default route is not on
            # eth0, we certainly have a directly internet addressable lxc
            # BE NOT permissive
            rif = default_route.get('iface', 'eth0')
            if rif == 'eth0':
                permissive_mode = True
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.firewall.shorewall', {
                # mapping of list of mappings
                'interfaces': OrderedDict(),
                'params': OrderedDict(),
                'rules': [],
                'nat': [],
                'proxyarp': [],
                'policies': [],
                'zones': OrderedDict(),
                'masqs': [],
                'sw_ver': sw_ver,
                'default_params': OrderedDict(),
                'default_masqs': [],
                'default_interfaces': OrderedDict(),
                'default_policies': [],
                'default_rules': [],
                'banned_networks': [],
                'trusted_networks': [],
                'internal_zones': [],
                'default_zones': {'net': OrderedDict(),
                                  'fw': {'type': 'firewall'}},
                'no_default_masqs': False,
                'no_default_params': False,
                'no_default_interfaces': False,
                'no_default_policies': False,
                'no_default_rules': False,
                'no_default_zones': False,
                # list of mappings
                # dict of section/rule mappings parsed from rules
                '_rules': OrderedDict(),
                'no_default_net_bridge': False,
                'no_invalid': True,
                'no_snmp': False,
                'no_mongodb': False,
                'no_mysql': False,
                'no_salt': False,
                'no_mastersalt': False,
                'no_postgresql': False,
                'have_docker': None,
                'have_vpn': None,
                # backward compat
                'have_rpn': have_rpn,
                'have_lxc': None,
                'no_dns': False,
                'no_ping': False,
                'no_smtp': False,
                'no_ssh': False,
                'no_ntp': False,
                'no_web': False,
                'no_ldap': False,
                'no_ftp': False,
                'no_burp': False,
                'no_mumble': False,
                'no_syslog': False,
                'no_computenode': False,
                'defaultstate': 'new',
                'permissive_mode': permissive_mode,
                'ifformat': shwIfformat,
                'ulogd': ulogd,
                # retro compat
                'enabled': __salt__['mc_utils.get'](
                    'makina-states.services.shorewall.enabled', True),

            })
        info_loglevel = 'info'
        if data['ulogd']:
            info_loglevel = 'NFLOG'
        # alias for retrocompat
        data['shwInterfaces'] = data['interfaces']
        data['shwPolicies'] = data['policies']
        data['shwParams'] = data['params']
        data['shwZones'] = data['zones']
        data['shwMasqs'] = data['masqs']
        data['shwIfformat'] = data['ifformat']
        data['shwRules'] = data['rules']
        data['shwDefaultState'] = data['defaultstate']
        data['shwEnabled'] = data['enabled']
        data['shw_interfaces'] = data['interfaces']
        data['shw_policies'] = data['policies']
        data['shw_params'] = data['params']
        data['shw_zones'] = data['zones']
        data['shw_masqs'] = data['masqs']
        data['shw_rules'] = data['rules']
        data['shw_defaultState'] = data['defaultstate']
        data['shw_enabled'] = data['enabled']
        # search & autodetect for well known network interfaces bridges
        # to activate in case default rules for lxc & docker
        if data['have_lxc'] is None:
            if True in ['lxc' in a[0] for a in gifaces]:
                data['have_lxc'] = True  # must stay none if not found
        if data['have_docker'] is None:
            if True in ['docker' in a[0] for a in gifaces]:
                data['have_docker'] = True  # must stay none if not found
        if data['have_vpn'] is None:
            if True in [a[0].startswith('tun') for a in gifaces]:
                data['have_vpn'] = True  # must stay none if not found

        opts_45 = ',sourceroute=0'
        bridged_opts = 'routeback,bridge,tcpflags,nosmurfs'
        bridged_net_opts = (
            'bridge,tcpflags,dhcp,nosmurfs,routefilter')
        phy_opts = 'tcpflags,dhcp,nosmurfs,routefilter'
        if sw_ver >= '4.4':
            phy_opts += opts_45
            bridged_net_opts += opts_45
        iface_opts = {
            'vpn': '',
            'net': phy_opts,
            'rpn': phy_opts,
            'brnet': bridged_net_opts,
            'lxc': bridged_opts,
            'dck': bridged_opts,
        }
        # service access restrictions
        # enable all by default, but can by overriden easily in config
        # this will act at shorewall parameters in later rules
        burpsettings = __salt__['mc_burp.settings']()

        if not data['no_default_params']:
            for p in ['SYSLOG', 'SSH', 'SNMP', 'PING', 'LDAP', 'SALT',
                      'NTP', 'MUMBLE', 'DNS', 'WEB', 'MONGODB',
                      'BURP', 'MYSQL', 'POSTGRESQL', 'FTP']:
                default = 'fw:127.0.0.1'
                if p in ['SSH', 'DNS', 'PING', 'WEB', 'MUMBLE']:
                    default = 'all'
                if p == 'BURP':
                    default = 'net:'
                    bclients = prefered_ips(burpsettings['clients'])
                    default += ','.join(bclients)
                data['default_params'].setdefault(
                    'RESTRICTED_{0}'.format(p), default)
            for r, rdata in data['default_params'].items():
                data['params'].setdefault(r, rdata)

        # if we have no enough information, but shorewall is activated,
        # construct a simple firewall allowing ssh icmp, and web traffic
        if not data['no_default_zones']:
            if data['have_vpn']:
                data['default_zones']['vpn'] = OrderedDict()
            if data['have_lxc']:
                data['default_zones']['lxc'] = OrderedDict()
            if data['have_docker']:
                data['default_zones']['dck'] = OrderedDict()
            if data['have_rpn']:
                data['default_zones']['rpn'] = OrderedDict()
            for z, zdata in data['default_zones'].copy().items():
                if not zdata:
                    zdata = {'type': 'ipv4'}
                data['default_zones'][z] = zdata
                if z not in data['default_interfaces']:
                    data['zones'].setdefault(z, data['default_zones'][z])

        ems = [i
               for i, ips in gifaces
               if i.startswith('em') and len(i) in [3, 4]]

        has_br0 = 'br0' in [a[0] for a in gifaces]
        # add br0 to the net network even if it does not
        # exists to facilitate switchs from wired nic
        # to bridged nics
        if not data['no_default_net_bridge'] and not has_br0:
            gifaces.append(('br0', []))

        for iface, ips in gifaces:
            if 'lo' in iface:
                continue
            z = 'net'
            # TODO: XXX: find better to mach than em1
            if iface.startswith('tun'):
                z = 'vpn'
                data['have_vpn'] = True
            if (
                iface in ['eth1']
                or iface in ems
            ):
                if have_rpn:
                    realrpn = False
                    if iface in ems:
                        if iface == ems[-1]:
                            realrpn = True
                    else:
                        realrpn = True
                    if not providers['is']['online']:
                        realrpn = False
                    if realrpn:
                        z = 'rpn'
            if 'docker' in iface:
                if data['have_docker']:
                    z = 'dck'
            if iface == 'br0':
                z = 'brnet'
            if 'lxc' in iface:
                if data['have_lxc']:
                    z = 'lxc'
            zz = {'brnet': 'net'}.get(z, z)
            data['default_interfaces'].setdefault(zz, [])
            data['default_interfaces'][zz].append({
                'interface': iface, 'options': iface_opts[z]})
        for z, ifaces in data['default_interfaces'].items():
            for iface in ifaces:
                data['interfaces'].setdefault(z, [])
                if iface not in data['interfaces'][z]:
                    data['interfaces'][z].append(iface)
        default_lxc_docker_mode = 'masq'
        if default_lxc_docker_mode == 'masq':
            for z, ifaces in data['interfaces'].items():
                if 'lxc' in z or 'dck' in z:
                    for iface in ifaces:
                        mask = {'interface': default_if,
                                'source': iface['interface']}
                        if mask not in data['default_masqs']:
                            data['default_masqs'].append(mask)

        if not data['no_default_masqs']:
            # fw -> net: auth
            for m in data['default_masqs']:
                if m not in data['masqs']:
                    data['masqs'].append(m)

        if not data['no_default_policies']:
            # fw -> defined zones: auth
            for z in data['zones']:
                data['default_policies'].append({
                    'source': '$FW', 'dest': z, 'policy': 'ACCEPT'})

            for z in ['fw'] + [a for a in data['zones']]:
                if z not in data['internal_zones'] and z not in ['net']:
                    data['internal_zones'].append(z)

            # dck -> net: auth
            # dck -> dck: auth
            # lxc -> dck: auth
            # dck -> lxc: auth
            if data['have_vpn']:
                data['default_policies'].append({
                    'source': 'vpn', 'dest': '$FW', 'policy': 'ACCEPT'})
                data['default_policies'].append({
                    'source': '$FW', 'dest': 'vpn', 'policy': 'ACCEPT'})
                data['default_policies'].append({
                    'source': 'vpn', 'dest': 'all', 'policy': 'ACCEPT'})
                data['default_policies'].append({
                    'source': 'all', 'dest': 'vpn', 'policy': 'ACCEPT'})
            if data['have_docker']:
                data['default_policies'].append({
                    'source': 'dck', 'dest': 'net', 'policy': 'ACCEPT'})
                data['default_policies'].append({
                    'source': 'dck', 'dest': 'dck', 'policy': 'ACCEPT'})
            if data['have_docker'] and data['have_lxc']:
                data['default_policies'].append({
                    'source': 'dck', 'dest': 'lxc', 'policy': 'ACCEPT'})
                data['default_policies'].append({
                    'source': 'lxc', 'dest': 'dck', 'policy': 'ACCEPT'})

            # fw -> lxc: auth
            # lxc -> net: auth
            if data['have_lxc']:
                data['default_policies'].append({
                    'source': 'lxc', 'dest': 'net', 'policy': 'ACCEPT'})
                data['default_policies'].append({
                    'source': '$FW', 'dest': 'lxc', 'policy': 'ACCEPT'})

            # rpn -> all: drop
            # fw -> rpn: auth
            if data['have_rpn']:
                data['default_policies'].append({
                    'source': 'rpn', 'dest': 'all',
                    'policy': 'DROP', 'loglevel': info_loglevel})
                data['default_policies'].append({
                    'source': '$FW', 'dest': 'rpn', 'policy': 'ACCEPT'})

            # drop all traffic by default if not in permissive_mode
            if not data['permissive_mode']:
                data['default_policies'].append({
                    'source': 'all', 'dest': 'all',
                    'policy': 'REJECT', 'loglevel': info_loglevel})
                data['default_policies'].append({
                    'source': 'net', 'dest': 'all',
                    'policy': 'DROP', 'loglevel': info_loglevel})
            else:
                data['default_policies'].append({
                    'source': 'all', 'dest': 'all', 'policy': 'ACCEPT'})
                data['default_policies'].append({
                    'source': 'net', 'dest': 'all', 'policy': 'ACCEPT'})

        # ATTENTION WE MERGE, so reverse order to append at begin
        data['default_policies'].reverse()
        for rdata in data['default_policies']:
            if rdata not in data['policies']:
                data['policies'].insert(0, rdata)

        if not data['no_default_rules']:
            if nodetypes_registry['is']['lxccontainer']:
                if not data['trusted_networks']:
                    data['trusted_networks'].append('net:{0}/{1}'.format(
                        default_net, default_netmask))
            for network in data['banned_networks']:
                data['default_rules'].insert(
                    0, {'action': 'DROP!', 'source': network, 'dest': 'fw'})
            for network in data['trusted_networks']:
                data['default_rules'].insert(
                    0, {'action': 'ACCEPT!', 'source': network, 'dest': 'fw'})
            data['default_rules'].insert(0, {'comment': 'inter lxc traffic'})
            if sw_ver >= '4.5':
                data['default_rules'].append({'comment': 'invalid traffic'})
                if data['no_invalid']:
                    action = 'DROP'
                else:
                    action = 'ACCEPT'
                append_rules_for_zones(data['default_rules'], {
                    'action': get_macro('Invalid', action),
                    'source': 'net', 'dest': 'all'},
                    zones=data['internal_zones'])


        if not data['no_default_rules'] and not data['permissive_mode']:
            data['default_rules'].append({'comment': 'lxc dhcp traffic'})
            if data['have_lxc']:
                data['default_rules'].append(
                    {'action': 'ACCEPT',
                     'source': 'lxc', 'dest': 'fw',
                     'proto': 'udp', 'dport': '67:68'})
                data['default_rules'].append(
                    {'action': 'ACCEPT',
                     'source': 'fw', 'dest': 'lxc',
                     'proto': 'udp', 'dport': '67:68'})

            data['default_rules'].append({'comment': 'docker dhcp traffic'})
            if data['have_docker']:
                data['default_rules'].append(
                    {'action': 'ACCEPT',
                     'source': 'dck', 'dest': 'fw',
                     'proto': 'udp', 'dport': '67:68'})
                data['default_rules'].append(
                    {'action': 'ACCEPT',
                     'source': 'fw', 'dest': 'dck',
                     'proto': 'udp', 'dport': '67:68'})

            # salt/master traffic if any
            append_rules_for_zones(
                data['default_rules'],
                {'comment': '(Master)Salt on localhost'})
            for proto in protos:
                data['default_rules'].append(
                    {'action': 'ACCEPT',
                     'source': "$FW", 'dest': "$FW",
                     'proto': proto,
                     'dport': '4505,4506,4605,4606'})
            if data['have_lxc']:
                append_rules_for_zones(data['default_rules'],
                                       {'comment': '(Master)Salt on lxc'})
                for proto in protos:
                    data['default_rules'].append(
                        {'action': 'ACCEPT',
                         'source': "lxc", 'dest': "$FW",
                         'proto': proto,
                         'dport': '4505,4506,4605,4606'})
            if data['have_docker']:
                append_rules_for_zones(data['default_rules'],
                                       {'comment': '(Master)Salt on dockers'})
                for proto in protos:
                    data['default_rules'].append(
                        {'action': 'ACCEPT',
                         'source': "dck", 'dest': "$FW",
                         'proto': proto,
                         'dport': '4505,4506,4605,4606'})

            # enable compute node redirection port ange if any
            # XXX: this is far from perfect, now we open a port range which
            # will be avalaible for connection and the controller will use that
            cloud_c_settings = __salt__['mc_cloud_compute_node.settings']()
            is_compute_node = __salt__['mc_cloud_compute_node.is_compute_node']()
            if is_compute_node and not data['no_computenode']:
                cstart, cend = (
                    cloud_c_settings['ssh_port_range_start'],
                    cloud_c_settings['ssh_port_range_end'],
                )
                append_rules_for_zones(data['default_rules'],
                                       {'comment': 'corpus computenode'})
                for proto in protos:
                    append_rules_for_zones(
                        data['default_rules'],
                        {'action': 'ACCEPT',
                         'source': 'all', 'dest': 'fw',
                         'proto': proto,
                         'dport': (
                             '{0}:{1}'
                         ).format(cstart, cend)},
                        zones=data['internal_zones'])
            # enable mastersalt traffic if any
            if (
                controllers_registry['is']['mastersalt_master']
                and not data['no_mastersalt']
            ):
                data['default_rules'].append({'comment': 'mastersalt'})
                for proto in protos:
                    append_rules_for_zones(
                        data['default_rules'],
                        {'action': 'ACCEPT',
                         'source': 'all', 'dest': 'fw',
                         'proto': proto,
                         'dport': '4605,4606'},
                        zones=data['internal_zones'])
            # enable salt traffic if any
            if (
                (controllers_registry['is']['salt_master']
                 or controllers_registry['is']['mastersalt_master'])
                and not data['no_salt']
            ):
                    data['default_rules'].append({'comment': 'salt'})
                    for proto in protos:
                        append_rules_for_zones(
                            data['default_rules'],
                            {'action': 'ACCEPT',
                             'source': '$SALT_RESTRICTED_SALT',
                             'dest': 'fw',
                             'proto': proto,
                             'dport': '4605,4606'},
                            zones=data['internal_zones'])
                        append_rules_for_zones(
                            data['default_rules'],
                            {'action': 'ACCEPT',
                             'source': '$SALT_RESTRICTED_SALT',
                             'dest': 'fw',
                             'proto': proto,
                             'dport': '4505,4506'},
                            zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'dns'})
            if data['no_dns']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('DNS', action),
                 'source': 'all', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'web'})
            if data['no_web']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
                append_rules_for_zones(
                    data['default_rules'],
                    {'action': get_macro('Web', action),
                     'source': '$SALT_RESTRICTED_WEB', 'dest': 'all'},
                    zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'ntp'})
            if data['no_ntp']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('NTP', action),
                 'source': '$SALT_RESTRICTED_NTP', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'ssh'})
            if data['no_ssh']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('SSH', action),
                 'source': '$SALT_RESTRICTED_SSH',
                 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'syslog'})
            if data['no_syslog']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(data[
                'default_rules'],
                {'action': get_macro('Syslog', action),
                 'source': '$SALT_RESTRICTED_SYSLOG',
                 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'ping'})
            # restricting ping is really a awkard bad idea
            # for ping, we drop and only accept from restricted (default: all)
            # append_rules_for_zones(data['default_rules'], {
            #     'action': 'Ping(DROP)'.format(action),
            #     'source': 'net', 'dest': '$FW'})
            # if data['no_ping']:
            #     action = 'DROP'
            # else:
            #     action = 'ACCEPT'
            # append_rules_for_zones(data['default_rules'], {'action': 'Ping({0})'.format(action),
            #                               'source': '$SALT_RESTRICTED_PING',
            #                               'dest': '$FW'})
            # limiting ping
            # for ping, we drop and only accept from restricted (default: all)
            rate = 's:10/min:10'
            if sw_ver < '4.4':
                rate = '-'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('Ping', 'ACCEPT'),
                 'source': 'net',
                 'dest': '$FW',
                 'rate': rate},
                zones=data['internal_zones'])

            for z in [a for a in data['zones'] if a not in ['net']]:
                append_rules_for_zones(
                    data['default_rules'],
                    {'action': get_macro('Ping', 'ACCEPT'),
                     'source': z,
                     'dest': '$FW'},
                    zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'smtp'})
            if data['no_smtp']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('Mail', action),
                 'source': 'all', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'snmp'})
            if data['no_snmp']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('SNMP', action),
                 'source': '$SALT_RESTRICTED_SNMP', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'ftp'})
            if data['no_ftp']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('FTP', action),
                 'source': '$SALT_RESTRICTED_FTP', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'postgresql'})
            if data['no_postgresql']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('PostgreSQL', action),
                 'source': '$SALT_RESTRICTED_POSTGRESQL', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'mongodb'})
            if data['no_mongodb']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('mongodb', action),
                 'source': '$SALT_RESTRICTED_MONGODB', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'mysql'})
            if data['no_mysql']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('MySQL', action),
                 'source': '$SALT_RESTRICTED_MYSQL', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'mumble'})
            if data['no_mumble']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            for proto in protos:
                append_rules_for_zones(
                    data['default_rules'],
                    {'action': action,
                     'source': '$SALT_RESTRICTED_MUMBLE',
                     'dest': 'fw',
                     'proto': proto,
                     'dport': '64738'},
                    zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'ldap'})
            if data['no_ldap']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('LDAP', action),
                 'source': '$SALT_RESTRICTED_LDAP', 'dest': 'all'},
                zones=data['internal_zones'])
            append_rules_for_zones(
                data['default_rules'],
                {'action': get_macro('LDAPS', action),
                 'source': '$SALT_RESTRICTED_LDAP', 'dest': 'all'},
                zones=data['internal_zones'])

            data['default_rules'].append({'comment': 'burp'})
            if data['no_burp']:
                action = 'DROP'
            else:
                action = 'ACCEPT'
            for proto in protos:
                append_rules_for_zones(
                    data['default_rules'],
                    {'action': action,
                     'source': 'fw:127.0.0.1',
                     'dest': "all",
                     'proto': proto,
                     'dport': '4971,4972'},
                    zones=data['internal_zones'])
            for proto in protos:
                append_rules_for_zones(
                    data['default_rules'],
                    {'action': action,
                     'source': '$SALT_RESTRICTED_BURP',
                     'dest': "all",
                     'proto': proto,
                     'dport': '4971,4972'},
                    zones=data['internal_zones'])
            # also accept configured hosts
            burpsettings = __salt__['mc_burp.settings']()
            clients = 'net:'
            clients += ','.join(prefered_ips(burpsettings['clients']))
            for proto in protos:
                append_rules_for_zones(
                    data['default_rules'], {'action': action,
                                            'source': clients,
                                            'dest': "all",
                                            'proto': proto,
                                            'dport': '4971,4972'},
                    zones=data['internal_zones'])
        # ATTENTION WE MERGE, so reverse order to append at begin
        data['default_rules'].reverse()
        for rdata in data['default_rules']:
            if rdata not in data['rules']:
                data['rules'].insert(0, rdata)

        for i in data['rules']:
            section = i.get('section', data['defaultstate']).upper()
            if section not in data['_rules']:
                data['_rules'].update({section: []})
            data['_rules'][section].append(i)
        # prefix params with salt as it is shell
        params = data['params'].copy()
        data['params'] = OrderedDict()
        for p, value in params.items():
            data['params']['{0}_{1}'.format('SALT', p)] = value
        data['params_keys'] = [a for a in data['params']]
        data['params_keys'].sort()

        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
