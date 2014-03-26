{% set compute_node_settings= salt['mc_cloud_compute_node.settings']() %}
{% set cloudSettings= salt['mc_cloud.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
include:
  - makina-states.cloud.generic.hooks.vm
{% for target, vms in lxcSettings.vms.items() %}
{%  for vmname, data in vms.items() -%}
{% if compute_node_settings.targets[target].virt_types.lxc %}
{% set sname = '{0}-{1}'.format(target, vmname) %}
{% set cptslsname = '{1}/{0}/lxc/{2}/run-initial-highstate'.format(
        target.replace('.', ''),
        cloudSettings.compute_node_sls_dir,
        vmname.replace('.', '')) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
c{{sname}}-lxc.computenode.sls-generator-for-highstate:
  file.managed:
    - name: {{cptsls}}
    - user: root
    - mode: 750
    - makedirs: true
    - watch:
      - mc_proxy: cloud-generic-vm-pre-initial-highstate-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-pre-initial-highstate-deploy
    - contents: |
            include:
              - makina-states.cloud.generic.hooks.vm
            {% raw %}
            {% set msr = salt['mc_localsettings.settings']()['locations']['msr'] %}
            {% endraw%}
            {{sname}}-lxc-initial-highstate:
              cmd.run:
                - name: ssh {{vmname}} "{%raw%}{{msr}}{%endraw%}/_scripts/boot-salt.sh --initial-highstate"
                - user: root
                - watch:
                  - mc_proxy: cloud-{{vmname}}-generic-vm-pre-initial-highstate-deploy
                - watch_in:
                  - mc_proxy: cloud-{{vmname}}-generic-vm-post-initial-highstate-deploy
{%  endif %}
{% endfor %}
{% endfor %}
