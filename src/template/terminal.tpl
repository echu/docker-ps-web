<!doctype html>
<title>term.js</title>
<!--
  term.js
  Copyright (c) 2012-2013, Christopher Jeffrey (MIT License)
-->
<style>
  html {
    background: #555;
  }

  h1 {
    margin-bottom: 20px;
    font: 20px/1.5 sans-serif;
  }

/*
  .terminal {
    float: left;
    border: #000 solid 5px;
    font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
    font-size: 11px;
    color: #f0f0f0;
    background: #000;
  }

  .terminal-cursor {
    color: #000;
    background: #f0f0f0;
  }
*/
</style>
<h1>term.js</h1>
<script src="/term.js"></script>
<script>
(function() {
  window.onload = function() {
    var socket = new WebSocket("ws://" + location.host + "/ws/{{terminal_name}}")
    socket.onopen = function() {
      var term = new Terminal({
        cols: 80,
        rows: 24,
        useStyle: true,
        screenKeys: true,
        cursorBlink: false
      });

      term.on('data', function(data) {
        socket.send(data);
      });

      term.on('title', function(title) {
        document.title = title;
      });

      term.open(document.body);

      term.write('\x1b[31mWelcome to term.js!\x1b[m\r\n');

      socket.onmessage = function(e) {
        term.write(e.data);
      };

      socket.onclose = function() {
        term.destroy();
      };
    };
  };
}).call(this);
</script>
