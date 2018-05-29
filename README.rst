``xpynfo``
~~~~~~~~~~

This is a simple CLI tool to dump X window info in a tree format.

Current version is a proof-of-concept. The API will potentially change drastically.

Features
========

- Uses |anytree|_ to tidy output
- Uses |xcffib|_ for ``X`` interaction via ``XCB`` Python bindings
- Provides access to

  - |attributes|_
  - |geometry|_
  - |list_properties|_ with properties filled out via |get_properties|_

.. |anytree| replace:: the ``anytree`` package
.. _anytree: https://pypi.org/project/anytree/
.. |xcffib| replace:: the ``xcffib`` package
.. _xcffib: https://github.com/tych0/xcffib
.. |attributes| replace:: ``XGetWindowAttributes`` info
.. _attributes: https://tronche.com/gui/x/xlib/window-information/XGetWindowAttributes.html
.. |geometry| replace:: ``XGetGeometry`` info
.. _geometry: https://tronche.com/gui/x/xlib/window-information/XGetGeometry.html
.. |list_properties| replace:: ``XListProperties`` info
.. _list_properties: https://tronche.com/gui/x/xlib/window-information/XListProperties.html
.. |get_properties| replace:: ``xcb_get_property`` calls
.. _get_properties: https://www.systutorials.com/docs/linux/man/3-xcb_get_property/

Installation
============

.. code:: shell-session

    $ pip install --user xpynfo

Usage
=====

.. code:: shell-session

    $ export PATH=~/.local/bin:$PATH
    $ which xpynfo
    ~/.local/bin/xpynfo
    $ xpynfo --version
    xpynfo <version>
    $ xpynfo --help
    < dumps all the help >
    $ xpynfo \
        --recurse \
        --use-names \
        --style AsciiStyle \
        --max-depth 1 \
        --properties \
        $(xprop | awk '/WM_CLIENT_LEADER/{ print strtonum($NF); }')
    # Note: you have to click a window to populate xprop
    106954753: Sublime Text
    |   Properties:
    |       WM_CLASS: ['sublime_text', 'Sublime_text']
    |       WM_CLIENT_LEADER: 106954753
    |       WM_CLIENT_MACHINE: gxc-fedora-28.wotw
    |       WM_COMMAND: sublime_text
    |       WM_ICON_NAME: sublime_text
    |       WM_LOCALE_NAME: en_US.UTF-8
    |       WM_NAME: Sublime Text
    |       WM_NORMAL_HINTS: <WM_SIZE_HINTS>
    |       WM_PROTOCOLS: ['WM_DELETE_WINDOW', 'WM_TAKE_FOCUS', '_NET_WM_PING']
    |       _NET_WM_ICON_NAME: sublime_text
    |       _NET_WM_NAME: Sublime Text
    |       _NET_WM_PID: 637
    |       _NET_WM_USER_TIME_WINDOW: 106954754
    +-- 106954754



(Very Basic) Documentation
==========================

.. code::

    usage: xpynfo [-h] [-V] [-r] [-d MAX_DEPTH] [-a] [-g] [-p] [-n]
                  [-s {AsciiStyle,ContRoundStyle,ContStyle,DoubleStyle}]
                  [window_id]

    A tool to examine various pieces of X info. Without options the command simply
    prints the window id.

    positional arguments:
      window_id             Specify the window ID; default is the screen's root
                            window

    optional arguments:
      -h, --help            show this help message and exit
      -V, --version         Displays the package version and exits

    Scope Control:
      Options to control the scope of the calls xpynfo makes

      -r, --recurse         Also query children of the given ID recursively
      -d MAX_DEPTH, --max-depth MAX_DEPTH
                            Limit the depth of recursion

    X Calls:
      Options to add X information

      -a, --attributes      Add XWindowAttributes info to output
      -g, --geometry        Add XGetGeometry info to output
      -p, --properties      Add XListProperties combined with parsed XGetProperty
                            info to output

    Style:
      Options to tweak output look

      -n, --use-names       Add _NET_WM_NAME or WM_NAME (when available) to output
      -s {AsciiStyle,ContRoundStyle,ContStyle,DoubleStyle}, --style {AsciiStyle,ContRoundStyle,ContStyle,DoubleStyle}
                            Set the anytree rendering style
