-install with venv in dice
    source .venv/bin/activate
    pip3 install --user flask
    pip3 install --user sqlalchemy

    pip3 install --user --editable .
    add export FLASK_APP=spam
    and export FLASK_DEBUG=true
    to end of activate script

-run
    source .venv/bin/activate
    python3 -m flask run
    
you also need to have the echo server running if you want to send things over sockets or you'll get a connection refused



might need to install other packages
bluetooth (didnt install first try, gonna leave this
