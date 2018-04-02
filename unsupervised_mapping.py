__author__ = 'zqiu'
#############=====================================###################################
##mapping different types of synapses in the whole brain sections
#############=====================================###################################

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
import detection_common
import multiprocessing
from config import projects_dir,projects_dir_for_section_ZQ, projects_dir_for_section,n_processes,chunksize,XY_GRID,BOX_SIZE,PARAMS_TO_GRID,PARAMS_COLOC
import linecache
def convert_txt_to_mat(projects, instrument, sections, method, channel_params):
    # For Jess Andor data, by Ricky 18/07/2014
    # load metadata
    # md.tiles is a DataFrame with columns=["imagedir","tile_number","x_um","y_um","order_hint"]
    # md = metadata.section_metadata(instrument,mouse_id,section_id)
    channel,params = channel_params.items()[0]
    if channel == "SAP102":
        params_string = detection_common.method_param_string_SAP102(params)
        method_id = detection_common.method_method_id_SAP102(method,params)
    else:
        params_string = detection_common.method_param_string(params)
        method_id = detection_common.method_method_id(method,params)
    # select_mouse_path_list =  projects_dir_for_section_ZQ(projects,instrument,sections)#modified by Ricky
    select_mouse_path_list = projects_dir_for_section_ZQ(projects,instrument,sections,channel)

    for select_mouse_path in select_mouse_path_list:
        # metadata_path_list = glob(os.path.join(select_mouse_path,'*.txt'))#modified by Ricky
        # raw_col_num,raw_row_num = util.extract_map_dim(metadata_path_list[0])
        # tmp1 = linecache.getline(metadata_path_list[0],33).split(" ")# 33 for Human Cortical SDM
        # tmp1 = linecache.getline(metadata_path_list[0],90).split(" ")# 33 for Human Cortical SDM
        # raw_col_num = int(tmp1[-4])
        # raw_row_num = int(tmp1[-2])
        # zoom_factor = int(np.sqrt(len(XY_GRID)))
        mouse_folder_name = select_mouse_path.split("/")[-1] #-2 for Human Cotical SDM
        obj_path = os.path.join(projects,tilepath.derived_root,instrument,mouse_folder_name,method_id)
        # sums = np.zeros((raw_row_num*zoom_factor,raw_col_num*zoom_factor,len(PARAMS_TO_GRID)))
        # imagedir_map = np.zeros((raw_row_num*zoom_factor,raw_col_num*zoom_factor),dtype=np.int64)
        # count = 0
                # out template: stat_sums_GKD229_0048_C1_corsenobj_cf1.0_m1_ct0_mn6000_mx20000_m1Mean_m2Otsu.npy
        # mouse_id = mouse_folder_name.split("_")[1]#only valid for Jess data, need modification for other data!,by Ricky
        # section_id = mouse_folder_name.split("_")[-3]#only valid for Jess data, need modification for other data!,by Ricky
        # mouse_id = mouse_folder_name.split("_")[0]#only valid for Melissa data, need modification for other data!,by Ricky
        # section_id = mouse_folder_name.split("_")[1]#only valid for Melissa data, need modification for other data!,by Ricky
        mouse_id,section_id = mouse_folder_name.split("_")[0:2]
        # section_id = section_id.split("-")[0]
        if channel == "SAP102":
            filename_suffix = '{}_{}_{}_Ithresh{}'.format(
            mouse_id,
            section_id,
            detection_common.method_method_id_SAP102(method, params),
            Intensity_threshold
        )
        else:
            filename_suffix = '{}_{}_{}_Ithresh{}'.format(
            mouse_id,
            section_id,
            detection_common.method_method_id(method, params),
            Intensity_threshold
        )

        # sums_filename_npy = 'stat_sums_'+filename_suffix+'.npy'
        sums_filename_mat = 'obj'+filename_suffix+'.mat'#by Ricky
        stat_dir = os.path.join(projects,tilepath.derived_root,instrument,mouse_folder_name,"stats")#by Ricky
        util.makedirs_if_absent(stat_dir)


        args_stats = []
        count = 1
        print("******************do mapping on {} *******************************".format(select_mouse_path))
        t = time.time()
        for i in range(0,raw_row_num):
            for j in range(0,raw_col_num):
                args_stats.append((count,params_string,obj_path,Intensity_threshold,sums[i*zoom_factor:(i+1)*zoom_factor,j*zoom_factor:(j+1)*zoom_factor,:]))
                # get_statistics_method(args_stats[count - 1])
                count += 1

            # stat_dir = os.path.join(
            #     projects,
            #     tilepath.derived_root,
            #     instrument,
            #     tilepath.mouse_dirname(mouse_id),
            #     tilepath.section_dirname(section_id),
            #     "stats"
            # )
        # np.save(os.path.join(stat_dir,sums_filename_npy),sums)
        # sio.savemat(os.path.join(stat_dir,sums_filename_mat),{'sum_stats':sums})
        proc_pool = multiprocessing.Pool(n_processes)#open processors for parallel computing

        results = proc_pool.map(get_statistics_method,args_stats,chunksize)#the args must be an array of tuple!
        ## wrap the results
        empty_id_all = [i[2] for i in results[0:len(args_stats)]]
        count_id_all = [i[1] for i in results[0:len(args_stats)]]
        stats_all = [i[0] for i in results[0:len(args_stats)]]
        ind = 0
        for count in count_id_all.__iter__():#count start from 0
            temp_row = int(np.floor(count /raw_col_num))
            temp_col = np.mod(count,raw_col_num)
            sums[temp_row*zoom_factor:(temp_row+1)*zoom_factor,temp_col*zoom_factor:(temp_col+1)*zoom_factor,:] = stats_all[ind]
            # print('{}_{}'.format(temp_row,temp_col))
            # print(stats_all[ind][:,:,0])
            ind += 1
    # metadata_name = [name for name in os.listdir(select_mouse_path) if name.endswith('.txt')]#modified by Ricky
    #     image_path_list = glob(os.path.join(select_mouse_path,Image_suffix))#modified by Ricky
    #     np.save(os.path.join(stat_dir,sums_filename_npy),sums)
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
