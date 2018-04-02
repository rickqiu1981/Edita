
__author__ = 'zqiu'
#modified by Ricky 20/07/2015
import sys
sys.path.append("..")

import os
import time

import numpy as np
import scipy.io as sio
import pandas
from glob import glob
import tilepath
import util
# from corsen import corsen_param_string, corsen_method_id
from detection_constants import *
# import detection_common
import multiprocessing
from config import root_directory_raw,root_directory_output,XY_GRID,PARAMS_TO_GRID,PARAMS_COLOC,n_processes,chunksize,channel_list
# from config import projects_dir,projects_dir_for_section_ZQ, projects_dir_for_section,n_processes,chunksize,XY_GRID,BOX_SIZE,PARAMS_TO_GRID,PARAMS_COLOC
import linecache

_get_box_cache = {}

def  load_obj_csv(filename):
    # pandas uses the first col as index by default -- here this is "mouse"
    # which is not helpful
    objects_tmp = pandas.DataFrame.from_csv(filename, sep="\t")
                                            # , index_col=False)

    # empty dfs cause all sorts of problems, might as well just skip ....
    if objects_tmp.shape[0] == 0:
        return objects_tmp

    # drop some cols
    # drop some stuff to reduce memory requirement after join
    # going to assume that we know:
    # mouse, section, method, channel
    # irrelevant:
    # row
    # objects_tmp = objects_tmp.drop(["mouse","section","method","channel","row"],axis=1)
    return objects_tmp

def get_statistics_method(args):
                    # args_stats.append((count,temp_obj_filepath,sums[i*zoom_factor:(i+1)*zoom_factor,j*zoom_factor:(j+1)*zoom_factor,:]))

    count = args[0]
    obj_path = args[1]
    stats_sums = args[2]
    # zoom_factor = int(np.sqrt(len(XY_GRID)))
    # stats_sums = np.zeros((zoom_factor,zoom_factor,len(PARAMS_TO_GRID)))
    # if count == 106:
    #     tt =1
    print(obj_path)
    empty_id = 0
    try:
        if os.stat(obj_path).st_size > 0:
           obj_data = load_obj_csv(obj_path)
           if obj_data.shape[0] > 0:
                empty_id = 1
                obj_for_stats = obj_data
                stats_sums[0,0,0] += len(obj_for_stats)#counts for jess data, by Ricky
    except OSError:
        # print("the file {} is empty".format(obj_path))
        empty_id = 0
    return stats_sums,count - 1,empty_id
def get_statistics_method_coloc(args):
    count = args[0]
    obj_path = args[1]
    stats_sums = args[2]
    # if count == 106:
    #     tt =1
    empty_id = 0
    try:
        if os.stat(obj_path).st_size > 0:
            obj_data = load_obj_csv(obj_path)
            if obj_data.shape[0] > 0:
                empty_id = 1
                obj_for_stats = obj_data
                stats_sums[0,0,1] = sum(obj_for_stats.index.values<coloc_threshold)#counts for the statistics
    except OSError:
        # print("the file {} is empty".format(obj_path))
        empty_id = 0
    return stats_sums,count - 1,empty_id

def make_stat_images_coloc(
    section_root_path, channel_id,section_name):
    # For Jess Andor data, by Ricky 18/07/2014
    # load metadata
    # md.tiles is a DataFrame with columns=["imagedir","tile_number","x_um","y_um","order_hint"]
    # md = metadata.section_metadata(instrument,mouse_id,section_id)
    metadata_path_list = glob(os.path.join(section_root_path,'*.txt'))#modified by Ricky
    raw_col_num,raw_row_num = util.extract_map_dim(metadata_path_list[0])
    for channel in channel_id:
        channel_foldername  = channel_list[channel]
        section_path = os.path.join(section_root_path,'distance_results',channel_foldername)
        zoom_factor = int(np.sqrt(len(XY_GRID)))
        obj_path = section_path
        sums = np.zeros((raw_row_num*zoom_factor,raw_col_num*zoom_factor,len(PARAMS_TO_GRID)))
        filename_suffix = "{}_distance{:3d}nm".format(section_name,coloc_threshold)
     # sums_filename_npy = 'stat_sums_'+filename_suffix+'.npy'
        sums_filename_mat = 'stat_sums_'+filename_suffix+'.mat'#by Ricky
        stat_dir = os.path.join(section_root_path,root_directory_output,channel,"stats")#by Ricky
        util.makedirs_if_absent(stat_dir)
        sums = sio.loadmat(os.path.join(stat_dir,sums_filename_mat))['sum_stats']
    #===================start mapping ================================================================================>
        print("******************do tile coloc mapping on {} *******************************".format(section_path))
        t = time.time()
        ##==== list all txt files in the directory
        obj_files_list = [f for f in os.listdir(obj_path) if f.endswith('.csv')]
        ##===re-order the obj_files_list based on their number
        obj_number_list = []
        for obj_file in obj_files_list:
            temp_file = obj_file.split('_')
            if temp_file[-1].startswith('m'):
                obj_number_list.append(int(temp_file[-1][1:-4]))
            else:
                obj_number_list.append(int(temp_file[-2][1:]))
        obj_number_list = np.array(obj_number_list)
        new_order = np.argsort(obj_number_list)
        args_stats = []
        count = 1
        for i in range(0,raw_row_num):
            for j in range(0,raw_col_num):
                temp_obj_filepath = os.path.join(obj_path,obj_files_list[new_order[count - 1]])
                args_stats.append((count,temp_obj_filepath,sums[i*zoom_factor:(i+1)*zoom_factor,j*zoom_factor:(j+1)*zoom_factor,:]))
                # get_statistics_method_coloc(args_stats[count - 1])
                count += 1

    #=================MULTIPLE PROCESSING ======================
        proc_pool = multiprocessing.Pool(n_processes)#open processors for parallel computing
        results = proc_pool.map(get_statistics_method_coloc,args_stats,chunksize)#the args must be an array of tuple!
        ## wrap the results
        empty_id_all = [i[2] for i in results[0:len(args_stats)]]
        count_id_all = [i[1] for i in results[0:len(args_stats)]]
        stats_all = [i[0] for i in results[0:len(args_stats)]]
        ind = 0
        for count in count_id_all.__iter__():#count start from 0
            temp_row = int(np.floor(count /raw_col_num))
            temp_col = np.mod(count,raw_col_num)
            sums[temp_row*zoom_factor:(temp_row+1)*zoom_factor,temp_col*zoom_factor:(temp_col+1)*zoom_factor,:] = stats_all[ind]
            ind += 1
        sio.savemat(os.path.join(stat_dir,sums_filename_mat),{'sum_stats':sums})

            # stat_dir = os.path.join(
            #     projects,
            #     tilepath.derived_root,
            #     instrument,
            #     tilepath.mouse_dirname(mouse_id),
            #     tilepath.section_dirname(section_id),
            #     "stats"
            # )
    print("******************time cost is {} seconds *******************************".format(time.time() - t))

    # select_mouse_path_list =  projects_dir_for_section_ZQ(projects,instrument,sections)#modified by Ricky
    #     select_mouse_path_list = projects_dir_for_section_ZQ(projects,instrument,sections,channel)

def make_stat_images_trackmate(section_root_path, channel_id,section_name):
    # For trackmate, by Ricky 05/02/2016
    # load metadata
    # md.tiles is a DataFrame with columns=["imagedir","tile_number","x_um","y_um","order_hint"]
    # md = metadata.section_metadata(instrument,mouse_id,section_id)
    metadata_path_list = glob(os.path.join(section_root_path,'*.txt'))#modified by Ricky
    # metafile_size = 0
    metadata_path = ''
    for file in metadata_path_list:
        temp_imgname = file[0:-3] + 'tif'
        if not os.path.isfile(temp_imgname):
            metadata_path = file
            head,metadata_filename =os.path.split(metadata_path)
            break

    raw_col_num,raw_row_num = util.extract_map_dim(metadata_path)
    for channel in channel_id:
        # section_path = os.path.join(section_root_path,channel)
        section_path = os.path.join(section_root_path)
        zoom_factor = int(np.sqrt(len(XY_GRID)))
    # mouse_folder_name = select_mouse_path.split("/")[-1] #-2 for Human Cotical SDM
        obj_path = section_path
        sums = np.zeros((raw_row_num*zoom_factor,raw_col_num*zoom_factor,len(PARAMS_TO_GRID)))
        imagedir_map = np.zeros((raw_row_num*zoom_factor,raw_col_num*zoom_factor),dtype=np.int64)
        count = 0
        # section_id = section_id.split("-")[0]
        # if channel == "SAP102":
        #     filename_suffix = '{}_{}_{}_Ithresh{}'.format(
        #     mouse_id,
        #     section_id,
        #     detection_common.method_method_id_SAP102(method, params),
        #     Intensity_threshold
        # )
        # else:
        #     filename_suffix = '{}_{}_{}_Ithresh{}'.format(
        #     mouse_id,
        #     section_id,
        #     detection_common.method_method_id(method, params),
        #     Intensity_threshold
        # )
        # filename_suffix = "{}_distance{:3d}nm".format(section_name,coloc_threshold)
        filename_suffix = "{}".format(section_name)

     # sums_filename_npy = 'stat_sums_'+filename_suffix+'.npy'
        sums_filename_mat = 'stat_sums_'+filename_suffix+'.mat'#by Ricky
        stat_dir = os.path.join(root_directory_output,section_name,"stats")#by Ricky
        util.makedirs_if_absent(stat_dir)
        args_stats = []
        count = 1
    #===================start mapping ================================================================================>
        print("******************do tile mapping on {} *******************************".format(section_path))
        t = time.time()
        ##==== list all txt files in the directory
        obj_files_list = [f for f in os.listdir(obj_path) if f.endswith('.txt') and f != metadata_filename]
        ##===re-order the obj_files_list based on their number
        obj_number_list = []
        for obj_file in obj_files_list:
            # temp_imgname = obj_file[0:-3] + 'tif'
            # if os.path.isfile(os.path.join(obj_path,temp_imgname)):
            temp_file = obj_file.split('_')
            if temp_file[-1].startswith('m'):
                obj_number_list.append(int(temp_file[-1][1:-4]))
            else:
                obj_number_list.append(int(temp_file[-2][1:]))

        obj_number_list = np.array(obj_number_list)
        new_order = np.argsort(obj_number_list)
        args_stats = []
        count = 1
        for i in range(0,raw_row_num):
            for j in range(0,raw_col_num):
                temp_obj_filepath = os.path.join(obj_path,obj_files_list[new_order[count - 1]])
                args_stats.append((count,temp_obj_filepath,sums[i*zoom_factor:(i+1)*zoom_factor,j*zoom_factor:(j+1)*zoom_factor,:]))
                get_statistics_method(args_stats[count - 1])
                count += 1

    #=================MULTIPLE PROCESSING ======================
        # proc_pool = multiprocessing.Pool(n_processes)#open processors for parallel computing
        # results = proc_pool.map(get_statistics_method,args_stats,chunksize)#the args must be an array of tuple!
        # ## wrap the results
        # empty_id_all = [i[2] for i in results[0:len(args_stats)]]
        # count_id_all = [i[1] for i in results[0:len(args_stats)]]
        # stats_all = [i[0] for i in results[0:len(args_stats)]]
        # ind = 0
        # for count in count_id_all.__iter__():#count start from 0
        #     temp_row = int(np.floor(count /raw_col_num))
        #     temp_col = np.mod(count,raw_col_num)
        #     sums[temp_row*zoom_factor:(temp_row+1)*zoom_factor,temp_col*zoom_factor:(temp_col+1)*zoom_factor,:] = stats_all[ind]
        #     # print('{}_{}'.format(temp_row,temp_col))
        #     # print(stats_all[ind][:,:,0])
        #     ind += 1
        #=================end of MULTIPLE PROCESSING ======================
        sio.savemat(os.path.join(stat_dir,sums_filename_mat),{'sum_stats':sums})

            # stat_dir = os.path.join(
            #     projects,
            #     tilepath.derived_root,
            #     instrument,
            #     tilepath.mouse_dirname(mouse_id),
            #     tilepath.section_dirname(section_id),
            #     "stats"
            # )
    print("******************time cost is {} seconds *******************************".format(time.time() - t))
