from gevent import monkey
monkey.patch_all()

from gevent.coros import BoundedSemaphore
import gevent

import uuid
import os, os.path
import json
import time
import glob
import tarfile
import dockerps_client

from bottle import Bottle, abort, request, static_file, template

app = Bottle()

dockerps_servers = os.environ.get('DOCKERPS', '192.168.59.103:6728').split(',')

# maps container IDs to IPs
CONTAINERS = {}
ALL_CONTAINERS = []

def update_containers():
    global CONTAINERS
    global ALL_CONTAINERS
    ALL_CONTAINERS = []
    for server in dockerps_servers:
        with dockerps_client.client(server) as c:
            their_containers = c.containers()
            ALL_CONTAINERS.extend(their_containers)
            for container in their_containers:
                CONTAINERS[container['Id']] = server


@app.route("/")
def main():
    return static_file("index.html", root=os.getcwd() + "/static")

@app.route("/<filename>.js")
def javascripts(filename):
    return static_file("js/{}.js".format(filename), root=os.getcwd() + "/static")

@app.route("/<node_id>")
def terminal(node_id):

    try:
        CONTAINERS[node_id]
        return template("template/terminal", terminal_name = node_id)
    except KeyError:
        return json.dumps({"message": "no such node '%s' running" % (node_id)})

@app.route('/ws/containers')
def handle_containers():
    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        abort(400, 'Expected WebSocket request.')

    try:
        while True:
            update_containers()
            wsock.send(json.dumps(ALL_CONTAINERS))
            gevent.sleep(5)
    except WebSocketError as e:
        print e
    finally:
        #print "closing socket"
        wsock.close()

@app.route('/ws/<node_id>')
def handle_websocket(node_id):
    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        abort(400, 'Expected WebSocket request.')

    try:
        server = CONTAINERS[node_id]
        with dockerps_client.client(server) as c:
            c.shell(node_id, forward_socket=wsock)
    except WebSocketError as e:
        print e
    finally:
        #print "closing socket?"
        wsock.close()

#run(host='localhost', port=8080, debug=True, reloader=True, server='gevent')
from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler

server = WSGIServer(("0.0.0.0", 8080), app, handler_class=WebSocketHandler)
server.serve_forever()
