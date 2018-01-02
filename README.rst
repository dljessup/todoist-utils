=============
Todoist Utils
=============

This is a repository of utility programs I've written to use the Todoist API
to accomplish certain tasks that the base user interface doesn't do easily.

------------
Installation
------------

Follow the normal steps for installation of a Python 3 virtual environment::

    $ python3 -m venv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt

Additionally, you should copy config-example.ini to config.ini and post your
API key in that config file.

--------------
export-done.py
--------------

Generates a report of completed tasks in a given project.
