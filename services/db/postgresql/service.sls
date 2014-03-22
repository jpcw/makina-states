{%- import "makina-states/services/db/postgresql/hooks.sls" as hooks with context %}

include:
  - makina-states.settings.db.postgresql.hooks

{% set settings = salt['mc_pgsql.settings']() %}
{%- set default_user = settings.user %}
{% set orchestrate = hooks.orchestrate %}
{#-MAIN SERVICE RESTART/RELOAD watchers #}
makina-postgresql-service:
  service.running:
    - name: postgresql
    - watch:
      - mc_proxy: {{orchestrate['base']['postpkg']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postbase']}}

makina-postgresql-service-reload:
  service.running:
    - name: postgresql
    - enable: True
    - reload: True
    - require:
      - mc_proxy: {{orchestrate['base']['postpkg']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postbase']}}
    {# most watch requisites are linked here with watch_in #}
