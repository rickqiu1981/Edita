from __future__ import division

__author__ = 'atullo2'

import itertools, math, os, pprint, shutil, subprocess, sys, tempfile, zipfile

import cv2
import numpy as np
from scipy.io import loadmat
from PIL import Image, ImageDraw
import scipy, scipy.interpolate

# from pypuncta import config
# from pypuncta import datasets
# from pypuncta import metadata
# from pypuncta import tile_geometry_df
# from pypuncta import tilepath
# from pypuncta import util
import config#modified for windows, by Ricky 12/03/2014
# import metadata
import tile_geometry_df
import tilepath
import util
import time
sys.modules['tilepath'] = tilepath
import numpy as np
from glob import glob
# ds = datasets.datasets

_valid_roi_subdirs = ['ctxlayer','ctxarea','HipSubParaRight', 'HipSubPerpRight', 'HipSubPerpLeft', 'HipSubParaLeft']

# how many pixels does an intersection have to have before we count it?

_intersection_threshold = 1

def create_region_masks_ZQ(select_mouse_path,channel_id,scale):
    """ modified by Ricky
    Create bitmap masks for each region found for the section
    :select_mouse_path
    :param instrument:
    :param section:
    :param scale: Scale as px-per-tile
    """
    for channel in channel_id:
        temp_roi_dir = get_rois_ZQ(os.path.join(select_mouse_path,config.root_directory_output,channel,
            "masks"))

    # projects = config.projects_dir_for_section(ds, (mouse_id, section_id))

    # load metadata for section
    # md = metadata.section_metadata(instrument, mouse_id, section_id)

    # scale on which ROIs were drawn -- one tile = 64px
    # g = tile_geometry_df.tile_geometry(md.tiles,77.6,64)

        roi_pathnames = [
            os.path.join(temp_roi_dir,x) for x in os.listdir(temp_roi_dir)
            if x.endswith('.roi')
        ]
        mask_dir = os.path.join(select_mouse_path,config.root_directory_output,channel,
            "masks",
            "scale_{0:03d}".format(scale)
        )

        util.makedirs_if_absent(mask_dir)

    # AWTFIXME: assumes that ROIs were drawn on 16-fold downsizes
    # Andor image is 512 x 512 px tile,so the stitched tile becomes 32 x 32 px, by Ricky
        assert((32 % scale) == 0)
        scale_factor = 32/scale
    # sum = np.load(glob(os.path.join(select_mouse_path,"stats","*.npy"))[0])
        sum = loadmat(glob(os.path.join(select_mouse_path,config.root_directory_output,channel,"stats","*.mat"))[0])["sum_stats"]
        y,x,z = sum.shape
        get_roi_masks(
            roi_pathnames,
            mask_dir,
            x*scale_factor,
            y*scale_factor,
            config.ij_config,
            scale_factor
        )
        shutil.rmtree(temp_roi_dir)

def create_region_masks(instrument,section,scale):
    """
    Create bitmap masks for each region found for the section
    :param instrument:
    :param section:
    :param scale: Scale as px-per-tile
    """
    mouse_id, section_id = section
    temp_roi_dir = get_rois(mouse_id, section_id)

    projects = config.projects_dir_for_section(ds, (mouse_id, section_id))

    # load metadata for section
    md = metadata.section_metadata(instrument, mouse_id, section_id)

    # scale on which ROIs were drawn -- one tile = 64px
    g = tile_geometry_df.tile_geometry(md.tiles,77.6,64)

    roi_pathnames = [
        os.path.join(temp_roi_dir,x) for x in os.listdir(temp_roi_dir)
        if x.endswith('.roi')
    ]

    mask_dir = os.path.join(
        projects,
        tilepath.derived_root,
        instrument,
        tilepath.mouse_dirname(mouse_id),
        tilepath.section_dirname(section_id),
        "masks",
        "scale_{0:03d}".format(scale)
    )

    util.makedirs_if_absent(mask_dir)

    # AWTFIXME: assumes that ROIs were drawn on 16-fold downsizes
    # (i.e. where one 1024px tile becomes 64px)
    assert((64 % scale) == 0)
    scale_factor = 64/scale
    get_roi_masks(
        roi_pathnames,
        mask_dir,
        g["canvas_x"],
        g["canvas_y"],
        config.ij_config,
        scale_factor
    )

    shutil.rmtree(temp_roi_dir)

def get_rois_in_dir(in_dir,label,out_dir):
    """Get all roi files, unpacking zip archives"""
    files_to_check = os.listdir(in_dir)
    for filename in files_to_check:
        filepath = os.path.join(in_dir,filename)
        if filename.endswith('.roi'):
            sys.stderr.write("ROI! "+filepath+" -> "+out_dir+"\n")
            shutil.copy2(filepath, os.path.join(out_dir,label+'_'+filename))
        elif filename.endswith('.zip'):
            sys.stderr.write("ZIP! "+filepath+"\n")
            roi_zip = zipfile.ZipFile(filepath)
            roi_names = roi_zip.namelist()
            roi_zip.extractall(out_dir)
            new_roi_name_base = label+'_'+os.path.split(filename)[1][:-4]
            for roi_name in roi_names:
                new_roi_name = new_roi_name_base+'_'+roi_name
                os.rename(
                    os.path.join(out_dir,roi_name),
                    os.path.join(out_dir,new_roi_name)
                )
            roi_zip.close()
        else:
            sys.stderr.write("not ROI or .zip, skipping: "+filepath+"\n")

def get_rois(mouse_id, section_id):
    # hardwired to projects, intentionally

    # # root_roi_dir = os.path.join(
    # #     '/remote/projects/Imaging/processed/montage/Regions')
    # section_root, vol = ds["base"][(mouse_id,section_id)]#revised by Ricky for windows transplant
    # root_roi_dir = os.path.join(config.projects_dir[vol],"region")
    # section_dirname = '%s_Section_%03d' % (mouse_id,section_id)
    root_roi_dir = os.path.join(
        '/remote/projects/Imaging/processed/montage/Regions')
    section_dirname = '%s_Section_%03d' % (mouse_id,section_id)
    # open subdirectory and look for .roi and .zip files
    section_dir = os.path.join(root_roi_dir,section_dirname)
    if not os.path.isdir(section_dir):
        sys.stderr.write(section_dir+" does not exist or is not a directory\n")
    roi_out_dir = tempfile.mkdtemp(prefix='count_regions_roi_')
    roi_in_dirs = [('main',section_dir)]
    roi_in_dirs += [
        (subdir,os.path.join(section_dir,subdir))
        for subdir in _valid_roi_subdirs
        if os.path.isdir(os.path.join(section_dir,subdir))
    ]
    for label, d in roi_in_dirs:
        get_rois_in_dir(d,label,roi_out_dir)
    return roi_out_dir
def get_rois_ZQ(root_roi_dir):
    #for Jess Ketamin Andor SDM data
    # hardwired to projects, intentionally

    # # root_roi_dir = os.path.join(
    # #     '/remote/projects/Imaging/processed/montage/Regions')
    # section_root, vol = ds["base"][(mouse_id,section_id)]#revised by Ricky for windows transplant
    # root_roi_dir = os.path.join(config.projects_dir[vol],"region")
    # section_dirname = '%s_Section_%03d' % (mouse_id,section_id)
    # root_roi_dir = os.path.join(
    #     '/remote/projects/Imaging/processed/montage/Regions')
    # section_dirname = '%s_Section_%03d' % (mouse_id,section_id)
    # section_dirname = ''
    # open subdirectory and look for .roi and .zip files
    section_dir = root_roi_dir
    # section_dir = os.path.join(root_roi_dir,section_dirname)
    if not os.path.isdir(section_dir):
        sys.stderr.write(section_dir+" does not exist or is not a directory\n")
    roi_out_dir = tempfile.mkdtemp(prefix='count_regions_roi_')
    roi_in_dirs = [('main',section_dir)]
    roi_in_dirs += [
        (subdir,os.path.join(section_dir,subdir))
        for subdir in _valid_roi_subdirs
        if os.path.isdir(os.path.join(section_dir,subdir))
    ]
    for label, d in roi_in_dirs:
        get_rois_in_dir(d,label,roi_out_dir)
    return roi_out_dir
def get_roi_masks(roi_pathnames,out_dir,x,y,ij_config,scale_factor):
    in_paths_file = tempfile.NamedTemporaryFile(prefix='imagej_roi_mask_in_',delete=False)
    in_paths_file.write("\n".join(roi_pathnames))
    in_paths_file.close()
    # java_cmd = (
    #     'java -cp "%s:%s" '
    #     +'org.genes2cognition.ijplugin.RoiConverter %s %s %d %d') % (
    #     ij_config['puncta_src'],ij_config['ij_jar'],in_paths_file.name, out_dir, x, y)
    # java_cmd = (
    #     'java -jar %s'
    #     +'\\regionmask.jar %s %s %d %d') % (
    #     ij_config['plugins_dir'],in_paths_file.name, out_dir, x, y)#revised by Ricky Qiu, using jar package instead of class files
    java_cmd = (
        'java -jar "%s"'
        +'/regionmask.jar "%s" "%s" %d %d') % (
        ij_config['plugins_dir'],in_paths_file.name, out_dir, x, y)#revised by Ricky Qiu, using jar package instead of class files in Linux

    pprint.pprint(java_cmd,sys.stderr)
    ret = subprocess.call(java_cmd,shell=True)
    # we may have a partial result, in which case attempt to delete the output
    if ret != 0:
        raise subprocess.CalledProcessError(ret,java_cmd)
    # uncompressed mask TIFFs are ~1000 times the size of the compressed ones!
    out_x = int(math.ceil(x/scale_factor))
    cmd = 'mogrify -compress RLE -sample {0:d}x "{1}/*.tif"'.format(out_x,out_dir)
    # cmd = 'mogrify -compress RLE -sample {0:d}x {1}\\*.tif'.format(out_x,out_dir)#revised for windows by Ricky Qiu

    subprocess.call(cmd,shell=True)
    os.unlink(in_paths_file.name)

def divide_region(mask_data):
    '''
    Divides a masked region into a number of sensible chunks
    :param mask_data: region mask in
    :return: list of regions
    '''
    pixel_step = 20.0

    # skeletonize and divide perpendicular to skeleton
    skel = skeletonize(mask_data.copy())
    skel[skel != 0] = 255
    skel_points = np.argwhere(skel != 0)
    # remove points with duplicate x
    keep = np.ones(len(skel_points[:,0]), 'bool')
    diff = np.diff(skel_points[:,0])
    keep[1:] = (diff != 0)
    skel_points = skel_points[keep,:]
    # fit a cubic
    s = scipy.interpolate.UnivariateSpline(
        skel_points[:,0],skel_points[:,1],k=3,s=skel_points.shape[0]*2
    )
    x = np.arange(np.min(skel_points[:,0].flat),np.max(skel_points[:,0].flat))
    fx = s(x)
    fx[fx<0] = 0
    fx[fx>=skel.shape[1]] = skel.shape[1]-1
    # now divide by length
    pts = np.vstack((x,fx)).T
    pprint.pprint(pts)
    diffs = np.diff(pts,axis=0)
    dists = np.sqrt(diffs[:,0]**2 + diffs[:,1]**2)
    dists = np.insert(dists,0,0.0)
    cum_dists = np.cumsum(dists)
    targets = np.arange(0.0,cum_dists[-1],pixel_step)
    pt_dividers = set() # points at which to divide the volume
    idx = 0
    for t in targets:
        try:
            while cum_dists[idx] < t:
                idx += 1
            # difference index, just means we take the low end of the range
            pt_dividers.add(idx)
        except IndexError:
            pass # finished!
    # import image into PIL
    mask_data = mask_data.astype(np.uint32)
    mask_data[mask_data != 0] = 255
    im = Image.fromarray(mask_data,mode='I')
    d = ImageDraw.Draw(im)
    for p in pt_dividers:
        # divide along the line, perpendicular to the two adjacent points
        (offset,gradient) = line_from_pts(pts[p-1,:],pts[p+1,:])
        pt = pts[p,:]
        # now work out where perpendicular intersects the box
        line = line_intersect_box(0,0,skel.shape[0],skel.shape[1],gradient,offset)
        #d.line(line,fill="#707070")
        d.line([(line[0][1],line[0][0]),(line[1][1],line[1][0])],fill="#707070")
        d.point((pt[0],pt[1]),fill="#000000")

    # divide original region

    out = np.array(im)

    return list((out,))


def line_from_pts(pt1,pt2):
    # y = ax + b
    pt_diff = (pt2[0] - pt1[0], pt2[1] - pt1[1])
    a = pt_diff[1] / pt_diff[0]
    b = pt1[1] - a * pt1[0]
    return b, a

def line_intersect_box(top,left,bottom,right,gradient,offset):
    # work out where this goes through the edges of the image
    # compute all intersections and return a list
    intersect_pts = [
        ((bottom - offset) / gradient, bottom),
        ((top - offset) / gradient, top),
        (left, (left * gradient) + offset),
        (right, (right * gradient) + offset)
    ]
    return [
        pt for pt in intersect_pts
        if (left <= round(pt[0]) <= right)
            and (top <= round(pt[1]) <= bottom)
    ]

def intersect_regions(instrument,section,r1,r2,scale,label):
    """
    Produces all valid (i.e. non-zero area) intersections between two sets of areas
    (note: does not look for intersections *within* each set, just *between*)
    These will be saved in the standard location with the given label
    """
    mouse_id, section_id = section
    projects = config.projects_dir_for_section(ds, (mouse_id, section_id))

    mask_dir = os.path.join(
        projects,
        tilepath.derived_root,
        instrument,
        tilepath.mouse_dirname(mouse_id),
        tilepath.section_dirname(section_id),
        "masks",
        "scale_{0:03d}".format(scale)
    )

    def load_masks(label):
        return {
            f: np.array(cv2.imread(os.path.join(mask_dir,f),cv2.CV_LOAD_IMAGE_GRAYSCALE))
            for f in os.listdir(mask_dir)
            if f.startswith(label)
        }

    r1_masks, r2_masks = load_masks(r1), load_masks(r2)

    # generate a mask for each combination of the two
    created_files = [] # track for compression
    combinations = itertools.product(r1_masks.keys(),r2_masks.keys())
    for k1, k2 in combinations:
        mask_intersection = np.array(
            np.logical_and(r1_masks[k1],r2_masks[k2]),
            dtype=np.uint8
        ) # cast to uint8
        if np.sum(mask_intersection) > _intersection_threshold:#means the two masks intersect!by Ricky
            # make up a filename for the new mask
            # first, remove initial labels and .tif from existing filenames
            l1, l2 = k1.split('_',1)[1][:-4], k2.split('_',1)[1][:-4]
            new_filename = label+'_'+l1+'_intersect_'+l2+'.tif'
            new_pathname = os.path.join(mask_dir,new_filename)
            #pprint.pprint('{0} for {1}'.format(np.sum(mask_intersection),new_filename))
            mask_intersection *= 255
            cv2.imwrite(
                new_pathname,
                mask_intersection
            )
            created_files.append(new_pathname)
    # quoted_created_files = ["'{}'".format(f) for f in created_files]
    quoted_created_files = ['"{}"'.format(f) for f in created_files]#modifided for windows by Ricky
    # cmd = "mogrify -compress RLE {0}".format(' '.join(quoted_created_files))#not work in windows, perhaps because the command is too long! by Ricky,use loop instead
    # subprocess.call(cmd,shell=True)

    for temp_filename in quoted_created_files:#for windows, by Ricky
        cmd = "mogrify -compress RLE {0}".format(''.join(temp_filename))
        ret = subprocess.call(cmd,shell=True)
        print cmd
        time.sleep(0.1)
