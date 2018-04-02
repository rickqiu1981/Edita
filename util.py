'''
Created on 29 Oct 2014

@author: zqiu
'''

import cPickle
import datetime
import errno
import inspect
import math
import os.path
import subprocess
#################################### revise by Ricky, 03/03/2014
# from pypuncta import tilepath
import tilepath
#################################################################
def path_split(in_path):
    # remove double separators
    double_sep = 2*os.path.sep
    while double_sep in in_path:
        in_path = in_path.replace(double_sep,os.path.sep)
    # remove leading & trailing separators
    in_path = in_path.strip(os.path.sep)
    return in_path.split(os.path.sep)

def relative_path(path_from,path_to):
    """return the relative path from path_from to path_to
    (both are assumed to be absolute paths and directories)"""
    # assert(path_from.startswith(os.path.sep))#revised for windows!
    # assert(path_to.startswith(os.path.sep))
    assert(path_from.startswith("C:"+os.path.sep))#revised for windows!
    assert(path_to.startswith("C:"+os.path.sep))

    path_from_list, path_to_list = path_split(path_from), path_split(path_to)
    while path_from_list[0] == path_to_list[0]:
        path_from_list.pop(0)
        path_to_list.pop(0)
    # go back by depth of 'from' path
    back_path = os.path.join(*(len(path_from_list)*['..']))
    # 'to' path
    forward_path = os.path.join(*path_to_list)
    return os.path.join(back_path,forward_path)

def script_name_from_stack():
    # inspect.stack() returns the call stack. The first entry is the caller,
    # the last is the top (which will be the script)
    # Each entry is a tuple, and the second element is the name
    return inspect.stack()[-1][1]

def script_version():
    return subprocess.check_output('svnversion .',shell=True).strip()

def timestamp(): # ISO
    return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

def log_message(log_dir,message):
    script_name = script_name_from_stack()
    if script_name.endswith('runfiles.py') or script_name.endswith('test.py'): # eclipse or cmd line test
        return
    # log_line = timestamp()+'\t Version '+script_version()+' of '+script_name+' '+message+'\n'#by ricky , svnversion not work in pycharm win7
    log_line = timestamp()+'\t Version Ricky'+' of '+script_name+' '+message+'\n'#by ricky , svnversion not work in pycharm win7

    log_file = open(os.path.join(log_dir,'log.txt'),'a')
    log_file.write(log_line)

def divide_list(stuff,n):
    chunk_size = int(math.ceil(float(len(stuff))/float(n)))
    return [stuff[x:x+chunk_size] for x in range(0,len(stuff),chunk_size)]

def itcn_param_id(cfg):
    # call throw_away "z" for "zero out"
    return "b%d_w%d_md%.0f_t%d_z%d" % (
        cfg['box_size'],
        cfg['width'],
        cfg['min_dist']*10,
        cfg['threshold'],
        cfg['throw_away']
    )

def makedirs_if_absent(path):
    try:
        os.makedirs(path)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise e

def savepkl(obj,path):
    f = open(path,'wb')
    cPickle.dump(obj,f,protocol=2)

def loadpkl(path):
    f = open(path,'rb')
    return cPickle.load(f)

def extract_map_dim(metadata_path):
    mp_found = False
    with open(metadata_path) as f:
        for l in f:
            if 'Montage Positions' in l:
                tmp1 = l.split()
                raw_col_num = int(tmp1[-4])
                raw_row_num = int(tmp1[-2])
                mp_found = True
                break
    assert mp_found, 'Montage Positions not found in {}'.format(metadata_path)
    return raw_col_num,raw_row_num