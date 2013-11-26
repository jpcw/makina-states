#
# Alias for bootstrap server to really mean 'not wired to mastersalt'
#
#
# Basic bootstrap is responsible for the setup of saltstack
# Be sure to double check any dependant state there to work if there is
# nothing yet on the VM as it is a "bootstrap stage".
#

include:
  - makina-states.bootstrap.server

makina-bootstrap-standalone-grain:
  grains.present:
    - name: makina.bootstrap.standalone
    - value: True
    - require:
      - service: salt-minion
