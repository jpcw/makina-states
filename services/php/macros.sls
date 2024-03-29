{# PHP specific macros
# * fpm_pool => create all states for a fpm php pool
# * minimal_index => generate an index.php in given doc_root
#}

{#
#   Remever that all macro kwargs are given to the mc_php.fpmpool_opts which is
#   the function that configures your FPM pool, you can give some extra
#   parameters where the main are below. If you want to tweak your install
#   So please read the code of the function when it's tweak time,
#   but normally the defaults are just sufficients.
#
#  In most cases:
#     - Only the "domain" and "doc_root" parameters should  be sufficient
#       if you follow the makina-states layout and use a separate pool per project
#
#   Nevertheless, the main args you can set/override are:
#
#   - domain
#       domain name (main project domain name aka ServerName or site name)
#   - doc_root
#        absolute path to a custom directory
#        (totally optionnal if you use the predefined layout)
#   - project_root
#       top level project directory (defaults to: docroot/..)
#       (totally optionnal if you use the predefined layout)
#   - pool_template_source
#       defaults to makina-states's one,
#       jinja template to construct the fpm pool configuration from
#   - open_basedir
#       directories to add to openbasedirs.
#       We are pretty restrictives by default.
#   - include_path
#       directories to add to include directories.
#       We are pretty restrictives by default.
#   - Any kwarg:
#       overrides the default data dictionnary given to the template
#       of the pool being rendered using jinja, you can then either add
#       your custom variable returned by  mc_php.settings or override any
#       existing one.
#   - use_shared_socket_path
#       Do we use the fpm shared socket path (multiple projects share the same pool)
#
#   /path/to/docroot/
#   /path/to/
#           \_ docroot  <- doc_root
#           \_ tmp      <- tmp files
#           \_ private  <- private dir
#           \_ log      <- logs (fpm ppol)
#           \_ run      <- socket(s) & other runtime files path
#
#}
{% set ugs = salt['mc_usergroup.settings']() %}
{% set apacheData = salt['mc_apache.settings']() %}
{% set locs = salt['mc_locations.settings']() %}

{% macro fpm_pool(domain, doc_root) %}
{% set data = salt['mc_php.fpmpool_settings'](
                          domain, doc_root, **kwargs) %}
{% set sdata = salt['mc_utils.json_dump'](data) %}
# Pool file
makina-php-pool-{{ data.pool_name }}:
  file.managed:
    - user: root
    - group: root
    - mode: 664
    - name: {{ data.etcdir }}/fpm/pool.d/{{ data.pool_name }}.conf
    - source: {{ data.pool_template_source }}
    - template: 'jinja'
    - defaults:
        data: |
              {{sdata}}
    - require:
      - mc_proxy: makina-php-post-inst
    - watch_in:
      - mc_proxy: makina-php-pre-restart

makina-php-pool-{{ data.pool_name }}-logrotate:
  file.managed:
    - name: "{{locs.conf_dir}}/logrotate.d/fpm.{{data.pool_name}}.conf"
    - source: salt://makina-states/files/etc/logrotate.d/fpmpool.conf
    - template: jinja
    - defaults:
        name: {{data.pool_name}}
        logdir: {{data.log_dir}}
        rotate: {{data.rotate}}
    - mode: 644
    - user: root
    - group: root
    - require:
      - mc_proxy: makina-php-post-inst
    - require_in:
      - mc_proxy: makina-php-pre-restart

makina-php-pool-{{ data.pool_name }}-directories:
  file.directory:
    - user: {{ data.fpm_user }}
    - group: {{data.fpm_group }}
    - mode: "2775"
    - makedirs: True
    - names:
      - {{ data.private_dir }}
      - {{ data.tmp_dir }}
      - {{ data.log_dir }}
      - {{ data.doc_root }}
    - require:
      - mc_proxy: makina-php-post-inst
    - require_in:
      - mc_proxy: makina-php-pre-restart
{%- endmacro %}

{# Generate a minimal index.php in the aforementionned doc_root #}
{% macro minimal_index(doc_root, domain='no domain', mode='unkown mode') %}
{{ doc_root }}-minimal-index:
  file.managed:
    - name: {{ doc_root }}/index.php
    - unless: test -e "{{ doc_root }}/index.php"
    - source:
    - contents: '<?php phpinfo(); ?>'
    - makedirs: true
    - user: {{ data.fpm_user }}
    - group: {{ data.fpm_group }}
    - watch:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-php-pre-conf
    - watch_in:
      - mc_proxy: makina-apache-post-conf
      - mc_proxy: makina-php-post-conf
{% endmacro %}
