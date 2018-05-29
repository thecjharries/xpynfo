# coding=utf-8
# pylint:disable=missing-docstring
# pylint:disable=invalid-name
# pylint:disable=misplaced-comparison-constant

from __future__ import print_function

from argparse import ArgumentParser
from struct import unpack_from
from sys import argv

# pylint:disable=unused-import
import xcffib
from xcffib import connect
import xcffib.xproto
from xcffib.xproto import Atom, GetPropertyType
# pylint:enable=unused-import

from anytree import Node
from anytree.render import AsciiStyle, ContRoundStyle, ContStyle, DoubleStyle, RenderTree
from pkg_resources import require as pkg_require


CONNECTION = connect()
ATOM_CACHE = {}


def intern_atom(atom_name):
    if atom_name not in ATOM_CACHE:
        ATOM_CACHE[atom_name] = CONNECTION.core.InternAtom(
            False,
            len(atom_name),
            atom_name,
        ).reply().atom
        ATOM_CACHE[ATOM_CACHE[atom_name]] = atom_name
    return ATOM_CACHE[atom_name]

STRING_ATOMS = [
    Atom.STRING,
    intern_atom('UTF8_STRING'),
]

PROPERTY_UNPACK_NOTATION = {
    Atom.CARDINAL: 'I',
    Atom.INTEGER: 'I',
    Atom.WINDOW: 'I',
}

PREFERRED_SCREEN = CONNECTION.get_setup().roots[CONNECTION.pref_screen]

WINDOW_NODES = {}

LONG_OFFSET = 0
LONG_LENGTH = (2 ** 32) - 1
STYLE_CLASS_MAP = {
    'AsciiStyle': AsciiStyle,
    'ContRoundStyle': ContRoundStyle,
    'ContStyle': ContStyle,
    'DoubleStyle': DoubleStyle,
}


def get_atom_name(atom):
    if atom not in ATOM_CACHE:
        atom_name = CONNECTION.core.GetAtomName(atom).reply().name.to_string()
        ATOM_CACHE[atom] = atom_name
        ATOM_CACHE[atom_name] = atom
    return ATOM_CACHE[atom]


def dump_object(object_to_dump):
    for key in dir(object_to_dump):
        print(key, getattr(object_to_dump, key))


def unpack_property_value(reply_object):
    if not reply_object.value:
        return None
    value = unpack_from(
        PROPERTY_UNPACK_NOTATION[reply_object.type],
        reply_object.value.buf(),
    )
    if 1 == len(value):
        return value[0]
    return value


def get_property(window_id, atom_id):
    atom_name = get_atom_name(atom_id)
    prop_reply = CONNECTION.core.GetProperty(
        delete=False,
        window=window_id,
        property=atom_id,
        type=GetPropertyType.Any,
        long_offset=LONG_OFFSET,
        long_length=LONG_LENGTH,
    ).reply()
    if Atom.ATOM == prop_reply.type:
        list_of_atoms = prop_reply.value.to_atoms()
        atom_value = []
        for child_atom_id in list_of_atoms:
            atom_value.append(get_atom_name(child_atom_id))
    elif prop_reply.type in STRING_ATOMS:
        atom_value = prop_reply.value.to_string().strip(chr(0)).split(chr(0))
    else:
        try:
            atom_value = unpack_property_value(prop_reply)
        except KeyError:
            if prop_reply.type > 0:
                atom_value = "<{}>".format(get_atom_name(prop_reply.type))
            else:
                atom_value = '<binary>'
    if atom_value and hasattr(atom_value, '__len__') and 1 == len(atom_value):
        atom_value = atom_value[0]
    return atom_name, atom_value


def get_wm_name(window_id):
    _, wm_name = get_property(window_id, Atom.WM_NAME)
    return wm_name


def get_net_wm_name(window_id):
    _, net_wm_name = get_property(window_id, intern_atom('_NET_WM_NAME'))
    return net_wm_name


def define_window_names(window_id, discover=True):
    if discover:
        return get_net_wm_name(window_id), get_wm_name(window_id)
    return None, None


def define_properties(window_id, discover=True):
    properties = {}
    if discover:
        atoms = CONNECTION.core.ListProperties(window_id).reply().atoms
        for atom_id in atoms:
            atom_name, atom_value = get_property(window_id, atom_id)
            properties[atom_name] = atom_value
    return properties


def define_generic_member_dict(window_id, discover=True, cookie_call=None):
    member_dict = {}
    if discover:
        raw_reply = cookie_call(window_id).reply()
        for key in [
                key
                for key
                in dir(raw_reply)
                if not key.startswith('_')
        ]:
            member_dict[key] = getattr(raw_reply, key)
    return member_dict


def define_attributes(window_id, discover=True):
    return define_generic_member_dict(
        window_id=window_id,
        discover=discover,
        cookie_call=CONNECTION.core.GetWindowAttributes,
    )


def define_geometry(window_id, discover=True):
    return define_generic_member_dict(
        window_id=window_id,
        discover=discover,
        cookie_call=CONNECTION.core.GetGeometry,
    )

PARAMETER_META_MAP = {
    'list_properties': {
        'callback': define_properties,
        'member_dict': 'properties',
    },
    'get_window_attributes': {
        'callback': define_attributes,
        'member_dict': 'attributes',
    },
    'get_geometry': {
        'callback': define_geometry,
        'member_dict': 'geometry',
    },
}


def create_node_from_window(
        window_id,
        parent=None,
        recurse=True,
        max_depth=None,
        use_names=True,
        **kwargs
):  # pylint:disable=too-many-locals
    net_wm_name, wm_name = define_window_names(window_id, use_names)
    preferred_name = (net_wm_name or wm_name)
    if use_names and preferred_name:
        pretty_name = "{}: {}".format(window_id, preferred_name)
    else:
        pretty_name = window_id
    args = {
        'name': window_id,
        'parent': parent,
        'pretty_name': pretty_name,
        'wid': window_id,
    }
    for key, value in list(PARAMETER_META_MAP.items()):
        discover = kwargs[key] if key in kwargs else key not in kwargs
        args[value['member_dict']] = value['callback'](window_id, discover)
    WINDOW_NODES[window_id] = Node(**args)
    can_recurse = (
        recurse
        and
        (
            max_depth is None
            or
            WINDOW_NODES[window_id].depth < max_depth
        )
    )
    if can_recurse:
        child_windows = CONNECTION.core.QueryTree(window_id).reply().children
        for child in child_windows:
            create_node_from_window(
                window_id=child,
                parent=WINDOW_NODES[window_id],
                recurse=can_recurse,
                max_depth=max_depth,
                use_names=use_names,
                **kwargs
            )
    return WINDOW_NODES[window_id]


def build_tree_member_list(
        fill,
        node,
        style,
        member_dict,
        pretty_name=None,
        **kwargs
):  # pylint:disable=unused-argument
    if not hasattr(node, member_dict) or not getattr(node, member_dict):
        return []
    if pretty_name is None:
        pretty_name = "{}{}".format(
            member_dict[0].capitalize(),
            member_dict[1:],
        )
    pre = "{}{}".format(
        fill.encode('utf-8'),
        (
            style.vertical.encode('utf-8') if node.children
            else ''
        ),
    )
    lines = ["{}{}:".format(pre, pretty_name)]
    pre += ' ' * len(style.vertical)
    for key, value in sorted(list(getattr(node, member_dict).items())):
        lines.append("{}{}: {}".format(pre, key, value))
    return lines


def render_tree(
        tree,
        style=ContStyle,
        **kwargs
):
    render = RenderTree(tree, style=style)
    lines = []
    for pre, fill, node in render:
        lines.append("{}{}".format(pre.encode('utf-8'), node.pretty_name))
        for key, value in list(PARAMETER_META_MAP.items()):
            if (key in kwargs and kwargs[key]) or key not in kwargs:
                lines += build_tree_member_list(
                    fill=fill,
                    node=node,
                    style=render.style,
                    **value
                )
    return '\n'.join(lines)


def parse_args(args=None):
    if args is None:
        args = argv[1:]
    parser = ArgumentParser(
        description='A tool to examine various pieces of X info. '
                    'Without options the command simply prints the window id.',
        add_help=True
    )
    parser.add_argument(
        '-V', '--version',
        action='version',
        version="%(prog)s {}".format(pkg_require('xpynfo')[0].version),
        help='Displays the package version and exits',
    )
    scope_options = parser.add_argument_group(
        title='Scope Control',
        description='Options to control the scope of the calls xpynfo makes',
    )
    scope_options.add_argument(
        '-r', '--recurse',
        dest='recurse',
        action='store_true',
        help='Also query children of the given ID recursively',
    )
    scope_options.add_argument(
        '-d', '--max-depth',
        dest='max_depth',
        action='store',
        type=int,
        default=None,
        help='Limit the depth of recursion',
    )
    output_options = parser.add_argument_group(
        title='X Calls',
        description='Options to add X information',
    )
    output_options.add_argument(
        '-a', '--attributes',
        dest='attributes',
        action='store_true',
        help='Add XWindowAttributes info to output',
    )
    output_options.add_argument(
        '-g', '--geometry',
        dest='geometry',
        action='store_true',
        help='Add XGetGeometry info to output',
    )
    output_options.add_argument(
        '-p', '--properties',
        dest='properties',
        action='store_true',
        help='Add XListProperties combined with parsed XGetProperty info to output',
    )
    parser.add_argument(
        'window_id',
        nargs='?',
        action='store',
        default=PREFERRED_SCREEN.root,
        help="Specify the window ID; default is the screen's root window",
    )
    styling_options = parser.add_argument_group(
        title='Style',
        description='Options to tweak output look',
    )
    styling_options.add_argument(
        '-n', '--use-names',
        dest='use_names',
        action='store_true',
        help='Add _NET_WM_NAME or WM_NAME (when available) to output',
    )
    styling_options.add_argument(
        '-s', '--style',
        dest='style',
        action='store',
        choices=['AsciiStyle', 'ContRoundStyle', 'ContStyle', 'DoubleStyle'],
        default='ContStyle',
        help='Set the anytree rendering style',
    )
    return parser.parse_args(args)


def cli():
    # root = create_node_from_window(PREFERRED_SCREEN.root)
    # print(render_tree(root))
    args = ['-h']
    args = None
    config = parse_args(args)
    create_args = {
        'window_id': int(config.window_id),
        'parent': None,
        'recurse': config.recurse,
        'max_depth': config.max_depth,
        'use_names': config.use_names,
        'style': STYLE_CLASS_MAP[config.style],
    }
    for key, value in list(PARAMETER_META_MAP.items()):
        if hasattr(config, value['member_dict']):
            create_args[key] = getattr(config, value['member_dict'])
    root = create_node_from_window(**create_args)
    print(render_tree(root, **create_args))

if '__main__' == __name__:
    cli()
