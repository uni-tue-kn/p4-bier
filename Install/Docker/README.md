# Docker setup

Run ```docker build -t <name> .``` to build the docker image. Some special settings have to be set to run the docker container (privileged mode, passing module libraries, and so on).

On os x (image name p4env, x11 server):

```docker run -d -it --privileged --name p4 -v /lib/modules:/lib/modules -e DISPLAY=docker.for.mac.localhost:0 p4env```

is sufficient.

To install the python dependencies run `pip2 install -r requirements.txt` inside the Implementation folder.
