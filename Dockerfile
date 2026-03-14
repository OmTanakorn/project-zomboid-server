FROM ich777/steamcmd:latest

LABEL maintainer="Project Zomboid Server"
LABEL description="Project Zomboid Dedicated Server - Build 42 Unstable"

# Steam App ID for Project Zomboid Dedicated Server
ENV APPID=380870
# Build 42 unstable beta branch
ENV GAME_PARAMS="-beta b42multiplayer"
ENV DATA_PERM=755
ENV UMASK=022

# Server configuration
ENV SERVER_NAME=servertest
ENV SERVER_PASSWORD=
ENV ADMIN_PASSWORD=PLEASE_CHANGE_THIS_PASSWORD
ENV MAX_PLAYERS=16
ENV MAX_RAM=4096m

# Expose Project Zomboid server ports
EXPOSE 16261/udp
EXPOSE 16262/udp

# Volume for persistent server data
VOLUME ["/serverdata/serverfiles"]

RUN mkdir -p /serverdata/serverfiles
