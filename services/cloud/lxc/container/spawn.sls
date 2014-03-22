{% import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
include:
  - makina-states.services.cloud.lxc.hooks
{% set cloudSettings= services.cloudSettings %}
{% set lxcSettings = services.lxcSettings %}
{% macro lxc_container(data) %}
{% set sname = data.get('state_name', data['name']) %}
{% set name = data['name'] %}
{% set dnsservers = data.get("dnsservers", ["8.8.8.8", "4.4.4.4"]) -%}
{{sname}}-lxc-deploy:
  cloud.profile:
    - name: {{name}}
    - profile: {{data.get('profile', 'ms-{0}-dir-sratch'.format(data['target']))}}
    {% if name in ['makina-states'] %}
    - unless: test -e /var/lib/lxc/{{name}}/roots/etc/salt/pki/master/minions/makina-states
    {% else %}
    - unless: test -e {{cloudSettings.prefix}}/pki/master/minions/{{name}}
    {% endif %}
    - watch:
      - mc_proxy: {{sname}}-lxc-deploy-start-hook
    - watch_in:
      - mc_proxy: {{sname}}-lxc-deploy-end-hook
    - minion: {master: "{{data.master}}",
               master_port: {{data.master_port}}}
    - dnsservers: {{dnsservers|yaml}}
{%    for var in ["from_container",
                   "snapshot",
                   "image",
                   "gateway",
                   "bridge",
                   "mac",
                   "ssh_gateway",
                   "ssh_gateway_user",
                   "ssh_gateway_port",
                   "ssh_gateway_key",
                   "ip",
                   "netmask",
                   "size",
                   "backing",
                   "vgname",
                   "lvname",
                   "script_args",
                   "dnsserver",
                   "ssh_username",
                   "password",
                   "lxc_conf",
                   "lxc_conf_unset"] %}
{%      if data.get(var) %}
    - {{var}}: {{data[var]}}
{%      endif%}
{%    endfor%}
{% endmacro %}
{% for target, containers in services.lxcSettings.containers.items() %}
{%  for k, data in containers.items() -%}
{%    set data = data.copy() %}
{%    do data.update({'state_name': '{0}-{1}'.format(target, k)})%}
{%    do data.update({'target': target})%}
{{ lxc_container(data) }}
{%  endfor %}
{% endfor %}