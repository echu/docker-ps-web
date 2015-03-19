# Docker PS server
This server just lists all containers running *in the cluster*. It accomplishes
this by connecting to all docker PS instances and querying them for container
information and populating a simple table.

It also forwards terminal connections via a websocket to any connected http
clients.
