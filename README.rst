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

System Dependencies
===================

The core features depend on ``libxcb``. |xcffib_docs|_ also mention ``libxcb-render``. I suspect the full list of ``xcb`` components is actually necessary, but I haven't checked from a fresh install yet.

Here's a good way to discover dependencies in the RPM world. You should be able to replace ``dnf`` with ``yum`` on older systems.

.. code:: shell-session

    $ sudo dnf install -y dnf-utils --allowerasing

    # For a full XCB install, use this as the first line instead
    # UNLISTED_DEPS=($(eval "echo 'xcb-'{'proto','util-*'}{'','-devel'}"));
    $ UNLISTED_DEPS=($(eval "echo xcb-util-renderutil{,-devel}")); \
        DEPS=($(\
            repoquery --requires --resolve python2-xcffib \
                | awk -F':' '\
                    /^[^:]*:[^:]*$/{ \
                        gsub("-[0-9]+$", "", $1); \
                        print $1; \
                    }' \
                | sort -u \
        )); \
        FULL_DEPS=( "${UNLISTED_DEPS[@]}" "${DEPS[@]}" "${DEPS[@]/%/-devel}" )
        eval sudo dnf install \
            --skip-broken \
            $(printf "'%s' " "${FULL_DEPS[@]}")

    Package xcb-util-renderutil-0.3.9-10.fc28.x86_64 is already installed, skipping.
    Package xcb-util-renderutil-devel-0.3.9-10.fc28.x86_64 is already installed, skipping.
    Package libxcb-1.13-1.fc28.x86_64 is already installed, skipping.
    Package libxcb-1.13-1.fc28.i686 is already installed, skipping.
    Package python2-2.7.15-1.fc28.x86_64 is already installed, skipping.
    Package python2-cffi-1.11.2-1.fc28.x86_64 is already installed, skipping.
    Package python2-six-1.11.0-3.fc28.noarch is already installed, skipping.
    Package libxcb-devel-1.13-1.fc28.x86_64 is already installed, skipping.
    Package python2-devel-2.7.15-1.fc28.x86_64 is already installed, skipping.
    No match for argument: python2-cffi-devel
    No match for argument: python2-six-devel
    Dependencies resolved.
    Nothing to do.
    Complete!

    # Or, for an even simpler full install,
    $ sudo dnf install 'libxcb*' 'xcb*'

I have no idea how to do this in other ecosystems. It should be possible in |debian|_ or |arch|_ with some tweaking.

.. |xcffib_docs| replace:: The ``xcffib`` docs
.. _xcffib_docs: https://github.com/tych0/xcffib#installation
.. |debian| replace:: the Debian world
.. _debian: https://askubuntu.com/questions/80655/how-can-i-check-dependency-list-for-a-deb-package
.. |arch| replace:: the Arch world
.. _arch: https://wiki.archlinux.org/index.php/Pacman/Tips_and_tricks#Getting_the_dependencies_list_of_several_packages

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
