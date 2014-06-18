{% set locs = salt['mc_locations.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set data = salt['mc_icinga.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

{% if data.modules.cgi.enabled %}

{% import "makina-states/services/http/nginx/init.sls" as nginx with context %}
{% import "makina-states/services/cgi/uwsgi/init.sls" as uwsgi with context %}
include:
  - makina-states.services.http.nginx
  - makina-states.services.cgi.uwsgi

# create a virtualhost in nginx
{{ nginx.virtualhost(domain=data.modules.cgi.nginx.virtualhost, **data.modules.cgi.nginx)}}

# configure uwsgi
{{ uwsgi.app(name=data.modules.cgi.uwsgi.name,
             config_file=data.modules.cgi.uwsgi.config_file,
             config_data=data.modules.cgi.uwsgi.config_data,
             enabled=data.modules.cgi.uwsgi.enabled) }}

{% endif %}