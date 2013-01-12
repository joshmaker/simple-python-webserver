Simple Webserver
=======================

A simple webserver written in Python, for educational use only. 
For a more full featured webserver consider the [Basic HTTP server](http://docs.python.org/2/library/basehttpserver.html) 
included in the Python standard library.

>>> # Launch a webserver running on port 8000
>>> from .server import SimpleServer
>>> SimpleServer(8000).serve_forever()
