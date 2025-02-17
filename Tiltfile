k8s_yaml(kustomize('kubernetes/tilt'))

k8s_resource(
  objects=['ledger:namespace'],
  new_name='namespace'
)

local_resource(
    name='config', resource_deps=['namespace'],
    cmd='kubectx docker-desktop && kubectl -n ledger create configmap config --from-file config/ --dry-run=client -o yaml | kubectl apply -f -'
)

local_resource(
    name='secret', resource_deps=['namespace'],
    cmd='kubectx docker-desktop && kubectl -n ledger create secret generic secret --from-file secret/ --dry-run=client -o yaml | kubectl apply -f -'
)

# api

docker_build('ledger-api', './api')
k8s_resource('api', port_forwards=['14469:80', '14437:5678'], resource_deps=['secret'])

# gui

docker_build('ledger-gui', './gui')
k8s_resource('gui', port_forwards=['4469:80'], resource_deps=['api'])

# daemon

docker_build('ledger-daemon', './daemon')
k8s_resource('daemon', port_forwards=['24437:5678'], resource_deps=['api'])

# cron

docker_build('ledger-cron', './cron')
k8s_resource('cron', port_forwards=['34437:5678'], resource_deps=['secret'])

# redis

k8s_resource('redis', port_forwards=['24469:6379'])
