how to install with venv in dice
    be in the folder with this readme
    source .venv/bin/activate
    pip3 install --user flask
    pip3 install --user sqlalchemy

    (you need the dot in this command)
    pip3 install --user --editable .

-run
    source .venv/bin/activate
    python3 -m flask run
-running on the server
    git checkout flask
    git pull
    go to spam folder
    sudo FLASK_APP=spam.py python3 -m flask run --host=0.0.0.0 --port=80

you also need to have the echo server running if you want to send things over sockets or you'll get a connection refused

might need to install other packages
bluetooth (didnt install first try, gonna leave this


TODO:
fix some minor problems withe flash messages
get communication with the ev3 working
follow the requirements to implement features
see code for inline todos
