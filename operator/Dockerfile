FROM nixos/nix:latest
COPY default.nix /default.nix
COPY luola_bot_operator.py /luola_bot_operator.py
RUN nix-env -i python3
RUN nix-env -i -f /default.nix
CMD python3 /luola_bot_operator.py
