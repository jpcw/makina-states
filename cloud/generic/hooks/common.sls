include:
  - makina-states.localsettings.users-hook

cloud-generic-pre:
  mc_proxy.hook:
    - watch:
      - mc_proxy: users-ready-hook
    - watch_in:
      - mc_proxy: cloud-generic-final

cloud-generic-final:
  mc_proxy.hook: []
