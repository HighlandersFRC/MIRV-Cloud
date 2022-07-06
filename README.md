# MIRV-Cloud
## Azure deployment info:
Host IP: 20.221.114.229
Port: 8080
Azure url: Deployed api: https://portal.azure.com/#@neaeraconsulting.com/resource/subscriptions/94de27ba-3bee-4589-b67b-76f7575ac235/resourceGroups/JFrye_rg_Linux_centralus/providers/Microsoft.ContainerInstance/containerGroups/elated-roentgen/overview
Image url: https://hub.docker.com/repository/docker/jacob6838/mirvapidev

## docker azure deployment example
https://docs.docker.com/cloud/aci-integration/
```
docker login
docker context create aci mirvacicontext
docker build -t jacob6838/webrtc .
docker push jacob6838/webrtc
docker --context mirvacicontext run -p 8080:8080 jacob6838/webrtc
```



