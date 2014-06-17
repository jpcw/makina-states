include:
  - makina-states.services.cgi.uwsgi.hooks

uwsgi-start:
  service.running:
    - name: uwsgi
    - enable: True
    - watch:
      - mc_proxy: uwsgi-pre-restart
    - watch_in:
      - mc_proxy: uwsgi-post-restart


