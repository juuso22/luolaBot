FROM nixos/nix:latest
COPY default.nix /default.nix
RUN nix-env -i -f /default.nix
COPY luola_bot_operator.py /luola_bot_operator.py
CMD python3 /luola_bot_operator.py
