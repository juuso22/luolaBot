FROM nixos/nix:latest
COPY default.nix /default.nix
COPY luola_bot.py /luola_bot.py
RUN nix-env -i -f /default.nix
CMD luolabot
