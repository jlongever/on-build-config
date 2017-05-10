#!/bin/bash +e

virtualBoxDestroyAll() {
  set +e
    for uuid in `vboxmanage list vms | awk '{print $2}' | tr -d '{}'`; do
        echo "shutting down vm ${uuid}"
        vboxmanage controlvm ${uuid} poweroff
        echo "deleting vm ${uuid}"
        vboxmanage unregistervm ${uuid}
      done
  set -e
}
# To resolve error message as below, which is a dirty worksspace
# Build 'virtualbox-ovf' errored: Error enabling VRDP: VBoxManage error: VBoxManage: error: The machine 'rackhd-ubuntu-14.04' is already locked for a session (or being unlocked)

virtualBoxDestroyAll
