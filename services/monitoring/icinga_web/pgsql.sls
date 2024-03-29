{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_icinga_web.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

{% if 'pgsql' == data.databases.web.type %}

{% import "makina-states/services/db/postgresql/init.sls" as pgsql with context %}

include:

  # install postgresql
  {% if data.has_pgsql %}
  - makina-states.services.db.postgresql
  {% else %}
  - makina-states.services.db.postgresql.hooks
  {% endif %}

# create database
{{ pgsql.postgresql_db(db=data.databases.web.name) }}

# add user
{{ pgsql.postgresql_user(name=data.databases.web.user,
                         password=data.databases.web.password,
                         db=data.databases.web.name) }}

# import schema
{% set tmpf = '/tmp/icinga-web.schema.sql' %}
icinga_web-import-pgsql-schema:
  file.managed:
    - name: {{tmpf}}
    - source: salt://makina-states/files/etc/icinga-web/schemas/icinga-web.pgsql-schema.sql
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - defaults:
      data: |
            {{sdata}}
  cmd.run:
    {% if 'socket' in data.databases.web %}
    - name: psql "postgresql://{{data.databases.web.user}}:{{data.databases.web.password}}@[{{data.databases.web.socket}}]/{{data.databases.web.name}}" -f "{{tmpf}}"
    {% else %}
    - name: psql "postgresql://{{data.databases.web.user}}:{{data.databases.web.password}}@{{data.databases.web.host}}:{{data.databases.web.port}}/{{data.databases.web.name}}" -f "{{tmpf}}"
    {% endif %}
    - watch:
      - file: icinga_web-import-pgsql-schema
      - mc_proxy: makina-postgresql-post-base
    - watch_in:
      - mc_proxy: icinga_web-pre-install

# check schema importation
{% set tmpf = '/tmp/icinga-web.check.sql' %}
icinga_web-check-pgsql-schema:
  file.managed:
    - name: {{tmpf}}
    - source: ''
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - contents: |
                #!/bin/bash
                sql_queries=(
                 "select 16=count(*) as ok from information_schema.tables where table_schema='public'"
                 "select 96=count(*) as ok from information_schema.table_constraints"
                 "select 28=count(*) as ok from pg_index as idx
                  join pg_class as i on i.oid = idx.indexrelid
                  join pg_namespace as ns on ns.oid = i.relnamespace and ns.nspname = any(current_schemas(false))"
                )
                for query in "${sql_queries[@]}"; do
                 {% if 'socket' in data.databases.web %}
                  res="$(echo "select row_to_json(row) from ($query) row;" | psql -t "postgresql://{{data.databases.web.user}}:{{data.databases.web.password}}@[{{data.databases.web.socket}}]/{{data.databases.web.name}}" | jq .ok)"
                 {% else %}
                  res="$(echo "select row_to_json(row) from ($query) row;" | psql -t "postgresql://{{data.databases.web.user}}:{{data.databases.web.password}}@{{data.databases.web.host}}:{{data.databases.web.port}}/{{data.databases.web.name}}" | jq .ok)"
                 {% endif %}
                 if [ "true" != "$res" ]; then
                  echo "Error with query \"$query;\"";
                  rm "{{tmpf}}";
                  exit 1;
                fi
                done;
                echo "OK";
                rm {{tmpf}};
                exit 0;

  cmd.run:
    - name: {{tmpf}}
    - watch:
       - cmd: icinga_web-import-pgsql-schema
       - file: icinga_web-check-pgsql-schema
    - watch_in:
       - mc_proxy: icinga_web-pre-install

# delete logs in the database
# TODO: it is not a good idea but doctrine compilation reset serial when 
# configuration change that produces "duplicate primary key in nsm_log"
{% set tmpf = '/tmp/icinga-web.clearlogs.sql' %}
icinga_web-clear-dblogs:
  file.managed:
    - name: {{tmpf}}
    - source: ''
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - contents: |
                #!/bin/bash
                sql_queries=(
                 'delete from nsm_log'
                )
                for query in "${sql_queries[@]}"; do
                 {% if 'socket' in data.databases.web %}
                  res="$(echo "$query;" | psql -t "postgresql://{{data.databases.web.user}}:{{data.databases.web.password}}@[{{data.databases.web.socket}}]/{{data.databases.web.name}}")"
                 {% else %}
                  res="$(echo "$query;" | psql -t "postgresql://{{data.databases.web.user}}:{{data.databases.web.password}}@{{data.databases.web.host}}:{{data.databases.web.port}}/{{data.databases.web.name}}")"
                 {% endif %}
                done;
                rm {{tmpf}};
                exit 0;

  cmd.run:
    - name: {{tmpf}}
    - watch:
       - cmd: icinga_web-check-pgsql-schema
       - file: icinga_web-clear-dblogs
    - watch_in:
       - mc_proxy: icinga_web-pre-install


{% endif %}
