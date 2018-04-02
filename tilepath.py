'''
Created on 9 Nov 2012

@author: atullo2
@modified by Ricky 16/07/2014
'''

import os.path, pprint, re, sys
from collections import namedtuple
from config import root_directory_output
captured_root = 'imaging_captured_projects2'
derived_root = root_directory_output

TileID = namedtuple(
    'TileID',
    ["root",
     "instrument",
     "mouse",
     "section",
     "imagedir",
     "method",
     "channel",
     "stacklevel",
     "filename"]
)

_tile_id_cache = {}

def tile_id_sort(t1,t2):
    """sort with EARLIEST TILES LAST"""
    condition1 = -cmp(t1.imagedir,t2.imagedir)
    if condition1 == 0:
        return -cmp(t1.filename,t2.filename)
    else:
        return condition1

def filter_for_zc(info,c,z):
    return {
            k: v for k, v in info.iteritems()
            if k.channel == c and k.stacklevel == z
    }

def tile_id_to_path(tile_id,projects_dir):
    return os.path.join(projects_dir,os.path.join(*tile_id[:9]))

def tile_id_from_path(str_path):
    _, canonical_path = breakpath(str_path)
    if not str_path in _tile_id_cache:
        _tile_id_cache[str_path] = TileID(*canonical_path)
    return _tile_id_cache[str_path]
    
def tile_id_from_path_no_zc(str_path):
    _, canonical_path = breakpath(str_path)
    return TileID(*canonical_path,channel='',stacklevel='')        
    
def breakpath(str_path):
    list_path = [x for x in str_path.split(os.path.sep)]
    list_path = [x for x in list_path if x != '']
    extras = []
    try: # strip extraneous path, but we'll return it
        while list_path[0] not in [captured_root, derived_root]:
            extras.append(list_path.pop(0))
    except IndexError:
        sys.stderr.write("Invalid path "+str_path+" in breakpath")
        sys.exit(-1)
    return (extras,list_path)

def original_to_derived(original_path,method):
    (extras,list_path) = breakpath(original_path)
    if len(list_path) == 5:
        list_path.append(method)
    list_path[5] = method
    list_path[0] = derived_root
    # AWTFIXME: This is Linux specific (using / as fs root)
    return os.path.sep+os.path.join(*(extras+list_path))

# ?? AWTFIXME: not used?
def get_canonical_dir(projects_dir,is_captured,instrument_id,mouse_id,section_id,imagedir_id):
    return os.path.join(
        projects_dir,
        (captured_root if is_captured else derived_root),
        instrument_id,
        mouse_dirname(mouse_id),
        section_dirname(section_id),
        imagedir_dirname(imagedir_id)
    )

def tile_ids_to_paths(projects_dir,pos_rows):
    return [
       os.path.join(projects_dir,os.path.join(*row[:9]))
       for row in pos_rows]

def channel_dirname(channel):
    return "C{:d}".format(channel)

def stacklevel_dirname(stacklevel):
    return "Z{:02d}".format(stacklevel)

def section_dirname(section):
    return "section_%04d" % section

def section_id(section_str):
    return int(section_str[-4:])

def imagedir_dirname(imagedir):
    return "imagedir_%04d" % imagedir

def imagedir_id(imagedir_str):
    return int(imagedir_str[-4:])

def source_image_dir(imagedir):
    return os.path.join(imagedir,'source_image')

def mouse_dirname(mouse_id):
    return "mouse_"+mouse_id

def mouse_id(mouse_dirname):
    return mouse_dirname[6:]

def get_sections(projects,root,instrument,mouse_id):
    """for convenience of the caller, return map of
    section number -> section dir
    """
    mouse_dir = os.path.join(projects,root,instrument,mouse_dirname(mouse_id))
    section_dir_list = os.listdir(mouse_dir)
    sections = {}
    for x in sorted(section_dir_list):
        if not x.startswith('section_'):
            continue
        sections[section_id(x)] = os.path.join(mouse_dir,x)
    return sections

def get_imagedirs(projects,root,instrument,section):
    """for convenience of the caller, return map of
    imagedir number -> imagedir number
    """
    mouse_id, section_id = section
    mouse_dir = os.path.join(projects,root,instrument,mouse_dirname(mouse_id))
    section_dir = os.path.join(mouse_dir,section_dirname(section_id))
    imagedir_dir_list = os.listdir(section_dir)
    imagedirs = {}
    for x in sorted(imagedir_dir_list):
        if not x.startswith('imagedir_'):
            continue
        imagedirs[imagedir_id(x)] = os.path.join(section_dir,x)
    return imagedirs

def tile_number(tile_id):
    return int(re.match('W1F(\d+)T.*',tile_id.filename).group(1))

def image_filename(_c,_z,_n):
    # channel, stack level, tile number
    return 'W1F{n}T0001{z}{c}.tif'.format(n=_n,c=_c,z=_z)

def tile_path(
        projects,root,instrument,mouse_id,section_id,imagedir_id,method,
        channel,stacklevel,tile_number
):
    c_str = channel_dirname(channel)
    z_str = stacklevel_dirname(stacklevel)
    n_str = "{:03d}".format(int(tile_number))
    return os.path.join(
        projects,
        root,
        instrument,
        mouse_dirname(mouse_id),
        section_dirname(section_id),
        imagedir_dirname(imagedir_id),
        method,
        c_str,
        z_str,
        image_filename(c_str,z_str,n_str)
    )
def tile_path_colocolization(
        projects,root,instrument,mouse_id,section_id,imagedir_id,method
        # ,stacklevel
):
    c_str = channel_dirname(channel)
    # z_str = stacklevel_dirname(stacklevel)
    # n_str = "{:03d}".format(int(tile_number))
    return os.path.join(
        projects,
        root,
        instrument,
        mouse_dirname(mouse_id),
        section_dirname(section_id),
        imagedir_dirname(imagedir_id),
        # image_filename(c_str,z_str,n_str)
    )#by Ricky for PPI and Pearson file
