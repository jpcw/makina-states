# -*- coding: utf-8 -*-
'''

.. _module_mc_mysql:

mc_mysql / mysql functions
============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import copy
import logging
import mc_states.utils

__name = 'mysql'

log = logging.getLogger(__name__)


def settings(**kwargs):
    '''
    mysql settings

    isPercona
        TDB
    isOracle
        TDB
    isMariaDB
        TDB
    number_of_table_indicator
        number of tables contained in the database
    port
        TBD
    user
        TBD
    group
        TBD
    root_passwd
        autogenerated root password (can be overriden before db install)
    sharedir
        TBD
    datadir
        TBD
    tmpdir
        TBD
    etcdir
        TBD
    logdir
        TBD
    basedir
        TBD
    sockdir
        TBD
    conn_host / conn_user / conn_pass
        autogenerated
        Connection settings, user/pass/host used by salt
        to manage users, grants and database creations
    character_set
        default character set on CREATE DATABASE (use utf8' not 'utf-8')
    collate
        default collate on CREATE DATABASE
    noDNS
        Avoid name resolution on connections checks, must-have.
        This is the skip-name-resolv option
    memory_usage_percent / available_mem
        the macro will compute magiccaly the settings to
        fit this percentage of full memory on the host. So by default it's 50%
        of all RAM on a dev envirronment and 85% for a production one where
        the MySQl server should be alone on a server. Then all others settings
        parameters in the 'tunning' key could be set to False to let the macro
        fill the gaps. If you set somtehing other than False for one of theses
        settings it will be used instead of the value computed by the macro,
        check the macro for details and comments on all theses parameters.
        Note the "_M" means Mo, so for 2Go of innodb_buffer_pool_size use
        2024, that is 2024Mo.
        Tweak the 'number_of_table_indicator' to adjust some settings
        automatically from that, for example several Drupal instances
        using a lot of fields
        could manage several hundreds of tables. <=== IMPORTANT
    myCnf
        MySQL default custom configuration (services.db.mysql)
        To override the default makina-states configuration file,
        Use the 'makina-states.services.mysql.cnf pillar/grain


    If you want to fine tune the mysql server, read the method
    to know non documented parameters to override, the code is well
    documented but spared from configuration from end users.
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings(**lkwargs):
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        mysql_reg = __salt__[
            'mc_macros.get_local_registry'](
                'mysql', registry_format='pack')
        rootpw = mysql_reg.setdefault(
            'root_password', __salt__['mc_utils.generate_password']())
        grains = __grains__
        pillar = __pillar__
        locs = __salt__['mc_locations.settings']()

        data = __salt__['grains.filter_by']({
            'Debian': {
                'packages': {
                    'main': 'mysql-server',
                    'dev': 'libmysqlclient-dev',
                    'python': 'python-mysqldb',
                    'php': 'php-mysql'
                },
                'use_mem': None,
                'service': 'mysql',
                'sharedir': locs['share_dir'] + '/mysql',
                'datadir': locs['var_lib_dir'] + '/mysql',
                'tmpdir': locs['tmp_dir'],
                'etcdir': locs['conf_dir'] + '/mysql/conf.d',
                'logdir': locs['var_log_dir'] + '/mysql',
                'basedir': locs['usr_dir'],
                'sockdir': locs['var_run_dir'] + '/mysqld'
            },
            'RedHat': {}}, grain='os_family')
        #
        # mangle the default dict
        #
        mode = __salt__['mc_utils.get']('default_env', 'dev')
        if 'devhost' in nodetypes_registry['actives']:
            mode = 'dev'
        data.update({
            'bind_address': '0.0.0.0',
            'mode': mode,
            'var_log': data['logdir'],
            'myCnf': None,
            'conn_host': 'localhost',
            'conn_user': 'root',
            'conn_pass': 'secret',
            'character_set': 'utf8',
            'collate': 'utf8_general_ci',
            'noDNS': True,
            'isPercona': False,
            'myCnf': "salt://makina-states/files/{etcdir}/local.cnf",
            'isOracle': True,
            'isMariaDB': False,
            'port': '3306',
            'user': 'mysql',
            'group': 'mysql',
            'root_passwd': rootpw,
            'number_of_table_indicator': 400,
            'innodb_flush_method': 'O_DSYNC',
            'innodb_flush_log_at_trx_commit': 1,
            'nb_connections': 25,
            'memory_usage_percent': 15,
        })
        if data['mode'] not in ['dev']:
            data.update({
                'number_of_table_indicator': 1000,
                'innodb_flush_method': 'O_DIRECT',
                'innodb_flush_log_at_trx_commit': 2,
                'nb_connections': 250,
                'memory_usage_percent': 30,
            })
        # Now let's do the autotuning magic:
        # Some heavy memory usage settings could be used on mysql settings:
        # Below are the rules we use to compute some default magic
        # values for tuning settings.
        # Note that you can enforce any of theses settings by putting
        # some value fro them in
        # mysqlSettings (so in the pillar for example).
        # The most important setting for this tuning is the amount of the
        # total memory you
        # allow for MySQL, given by the % of total memory set in
        # mysqlSettings.memory_usage_percent
        # So starting from total memory * given percentage we use
        # (let's call it available memory):
        # * innodb_buffer_pool_size: 50% of avail.
        # * key_buffer_size:
        # * query_cache_size: 20% of avail. limit to 500M as a starting point
        # # -- per connections
        # * max_connections -> impacts on per conn memory settings
        #   (which are big)
        # and number of tables and files opened
        # * innodb_log_buffer_size:
        # * thread_stack
        # * thread_cache_size
        # * sort_buffer_size
        # # -- others
        #  * tmp_table_size == max_heap_table_size : If working data memory for
        #    a request
        #               gets bigger than that then file backed temproray tables
        #               will be used(and it will, by definition, be big ones),
        #               the bigger the better but you'll need RAM, again.
        # * table_open_cache
        # * table_definition_cache
        # first get the Mo of memory, cpu and disks on the system
        full_mem = data.setdefault('full_mem', grains['mem_total'])
        nb_cpus = data.setdefault('nb_cpus', grains['num_cpus'])
        # Then extract memory that we could use for this MySQL server
        available_mem = data.setdefault(
            'available_mem', full_mem * data['memory_usage_percent'] / 100)
        pref = 'makina-states.services.db.mysql'
        data = __salt__['mc_utils.defaults'](pref , data)
        available_mem = data['available_mem']
        # Now for all non set tuning parameters try to fill the gaps
        # ---- NUMBER OF CONNECTIONS
        data.setdefault('nb_connections', 100)

        # ---- QUERY CACHE SIZE
        try:
            query_cache_size_M = int((available_mem / 5))
        except (ValueError, TypeError):
            query_cache_size_M = 500
            if query_cache_size_M > 500:
                query_cache_size_M = 500
        query_cache_size_M = data.setdefault(
            'query_cache_size_M', query_cache_size_M)

        # ---- INNODB BUFFER
        # Values cannot be used in default/context
        # as others as we need to compute from previous values
        innodb_buffer_pool_size_M = data.setdefault(
            'innodb_buffer_pool_size_M', int((available_mem / 2)))
        # Try to divide this buffer in instances of 1Go
        innodb_buffer_pool_instances = data.setdefault(
            'innodb_buffer_pool_instances',
            int(round((innodb_buffer_pool_size_M / 1024), 0)))
        if innodb_buffer_pool_instances < 1:
            innodb_buffer_pool_instances = 1
        data['innodb_buffer_pool_instances'] = innodb_buffer_pool_instances

        # Try to set this to 25% of innodb_buffer_pool_size
        data.setdefault(
            'innodb_log_buffer_size_M',
            int(round((innodb_buffer_pool_size_M / 4), 0)))

        data = __salt__['mc_utils.defaults'](
            'makina-states.services.db.mysql',
            data)
        data = __salt__['mc_utils.dictupdate'](data, lkwargs)
        if data['conn_user'] == 'root':
            data['conn_pass'] = data['root_passwd']
        # ------- INNODB other settings
        data.setdefault('innodb_flush_method', 'fdatasync')
        # recommended value is 2*nb cpu + nb of disks, we assume one disk
        data.setdefault('innodb_thread_concurrency',
                        int(nb_cpus + 1) * 2)
        # Should we sync binary logs at each commits or prey
        # for no server outage?
        data.setdefault('sync_binlog', 0)
        # innodb_flush_log_at_trx_commit
        #  1 = Full ACID, but slow, log written at commit + sync disk
        #  0 = log written every second + sync disk,
        #      BUT nothing at commit (kill of mysql can loose
        #      last transactions)
        #  2 = log written every second + sync disk,
        #      and log written at commit without sync disk
        #      (server outage can loose transactions)
        #
        # let users override default values
        #

        # --------- Settings related to number of tables
        # This is by default 8M, should store all tables and indexes
        if data['number_of_table_indicator'] < 251:
            innodb_additional_mem_pool_size_M = 8
        elif data['number_of_table_indicator'] < 501:
            innodb_additional_mem_pool_size_M = 16
        elif data['number_of_table_indicator'] < 1001:
            innodb_additional_mem_pool_size_M = 24
        else:
            innodb_additional_mem_pool_size_M = 32
        innodb_additional_mem_pool_size_M = data.setdefault(
            'innodb_additional_mem_pool_size_M',
            innodb_additional_mem_pool_size_M)
        # TABLE CACHE
        #  table_open_cache should be
        #           max joined tables in queries * nb connections
        #  table_cache is the old name now
        #       it's table_open_cache and by default 400
        #  the system open_file_limit may not be good enough
        #  If server crash try to tweak "sysctl fs.file-max"
        #  or check mysql ulimit
        #  Warning /etc/security/limits.conf is not read
        #  by upstart (it's for users)
        #  so the increase of file limits must be set in upstart script
        #  http://askubuntu.com/questions/288471/mysql-cant-open-files-after-updating-server-errno-24
        data.setdefault('table_definition_cache',
                        data['number_of_table_indicator'])
        table_open_cache = data.setdefault('table_open_cache',
                                           data['nb_connections'] * 8)
        # this should be table_open_cache * nb_connections
        data.setdefault('open_file_limit',
                        data['nb_connections'] * table_open_cache)
        # tmp_table_size: On queries using temporary data, is this data gets
        # bigger than then the temporary memory things becames real physical
        # temporary tablesand things gets very slow, but this must be some free
        # RAM when the request is running, so if you use something like
        # 1024Mo prey that queries using this amount
        # of temporary data are not running too often...
        data.setdefault('tmp_table_size_M',
                        int((data['available_mem'] / 10)))
        mysql_reg['root_password'] = data['root_passwd']
        __salt__['mc_macros.update_local_registry'](
            'mysql', mysql_reg, registry_format='pack')
        return data
    kwargs = copy.deepcopy(kwargs)
    for k in [a for a in kwargs]:
        if '__pub_' in k:
            kwargs.pop(k, '')
    return _settings(**kwargs)


def dump():
    return mc_states.utils.dump(__salt__,__name)


#
