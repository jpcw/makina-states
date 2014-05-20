{% set vmname = pillar.mccloud_vmname %}
{% set target = pillar.mccloud_targetname %}
{% set compute_node_settings = salt['mc_utils.json_load'](pillar.scnSettings) %}
{% set data = salt['mc_utils.json_load'](pillar.slxcVmData) %}
{% set cloudSettings = salt['mc_utils.json_load'](pillar.scloudSettings) %}
{% if 'lxc' not in compute_node_settings.virt_types %}
not-installed:
  mc_proxy.hook: []
{% else%}
{% do data.update({'state_name': '{0}-{1}'.format(target, vmname)})%}
{% do data.update({'target': target})%}
{% set dnsservers = data.get("dnsservers", ["8.8.8.8", "4.4.4.4"]) -%}
lxc-deploy:
  cloud.profile:
    - name: {{vmname}}
    - profile: {{data.get('profile', 'ms-{0}-dir-sratch'.format(data['target']))}}
    - unless: test -e {{cloudSettings.prefix}}/pki/master/minions/{{vmname}}
    - minion:
       master: {{data.master}}
       master_port: {{data.master_port}}
    - dnsservers: {{dnsservers}}
    {% for var in ["from_container", "snapshot", "image",
                   "gateway", "bridge", "mac", "lxc_conf_unset",
                   "ssh_gateway", "ssh_gateway_user", "ssh_gateway_port",
                   "ssh_gateway_key", "ip", "netmask",
                   "size", "backing", "vgname",
                   "lvname", "script_args", "dnsserver",
                   "ssh_username", "password", "lxc_conf"] -%}
    {%- if data.get(var) %}
    {# workaround for bizarious rendering bug with ' ...' at each variable end #}
    - {{var}}: {{data[var]}}
    {% endif -%}{% endfor %}
{# NO MORE USED WITH LXC 1.0
lxc-autostart-at-boot:
  salt.function:
    - require:
      - cloud: lxc-deploy
    - tgt: [{{target}}]
    - expr_form: list
    - name: cmd.run
    - arg: [{{"'{0}'".format(
"if [ ! -e /etc/lxc/auto ];then mkdir -p /etc/lxc/auto;fi;"
"ln -sf /var/lib/lxc/{vmname}/config /etc/lxc/auto/{vmname}.conf".format(vmname=vmname))}}]
#}
{%endif%}
