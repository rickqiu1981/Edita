__author__ = 'zqiu'
'''
 by Ricky 01/01/2015
'''

import csv, os, pprint, sys

import cv2
# import matplotlib.pyplot as plt
import time
import numpy as np
from scipy import ndimage
from scipy.io import savemat,loadmat
import config
# from detection_common import *
# from corsen_common import corsen_method_id
from detection_constants import *
# import datasets
import tilepath
# import matplotlib.pylab as plt
from pandas import DataFrame
from collections import OrderedDict
import util
from glob import glob
import stats_image_trackmate
# ds = datasets.datasets

# UM2_PER_FAKEINCH2 = UM_PER_FAKEINCH**2
# UM2_PER_Pixel2 = UM_PER_PX**2
class MaskSet():
    def __init__(self,mask_dir):
        self.images = {}
        self.mask_dir = mask_dir

    def load_image(self,mask_name):
        if not mask_name in self.images:
            mask_path = os.path.join(self.mask_dir,mask_name)
            self.images[mask_name] = cv2.imread(mask_path,cv2.CV_LOAD_IMAGE_GRAYSCALE)
            if self.images[mask_name] is None:
                pprint.pprint("Unable to load "+mask_path,sys.stderr)
        return self.images[mask_name]
def collect_distance(args):
    obj_path = args[0]
    distance_list = args[1]
    empty_id = 0
    try:
        if os.stat(obj_path).st_size > 0:
            obj_data = stats_image_trackmate.load_obj_csv(obj_path)
            if obj_data.shape[0] > 0:
                empty_id = 1
                distance_list.extend(obj_data.index.values.tolist())
                # stats_sums[0,0,1] = sum(obj_for_stats.index.values<coloc_threshold)#counts for the statistics
    except OSError:
        # print("the file {} is empty".format(obj_path))
        empty_id = 0
    # return stats_sums,count - 1,empty_id

    return distance_list
def make_region_stats_ZQ(
                select_mouse_path,
                section_name,
                mask_set,
                roi_sets,
                isflip = 'N'
        # projects,instrument,mouse_folder_name,channel,
        # detection_method, detection_params, mask_set,roi_sets,isflip = 'Y'#for Jess Data
):
    roi_set_description = ''.join(p for p in roi_sets)
                                  # if p != 'main')
    # mouse_id = mouse_folder_name.split("_")[1]#only valid for Jess data, need modification for other data!,by Ricky
    # section_id = mouse_folder_name.split("_")[-3]#only valid for Jess data, need modification for other data!,by Ricky
    # mouse_id,section_id,test_id = mouse_folder_name.split("_")
    filename_suffix = section_name+"_"+roi_set_description#by Ricky
    sums_filename = 'stat_sums_'+section_name+'.mat'
    stat_dir = os.path.join(
        select_mouse_path,
        "stats"
    )
    stat_path = os.path.join(stat_dir,sums_filename)
    stat_all = loadmat(stat_path)["sum_stats"]
    if isflip == "Y":
        stat_all = np.flipud(stat_all)
    stats_to_plot = [
        "count", "coloc"
    ]

    # create this as a dict of stat -> {region -> value} -- we'll save as CSV
    stats_table = {}
    to_plot = np.ones_like(stat_all)*np.nan

    # Recall here that data[:,:,0] is the raw count, data[:,:,1] is the count
    # for stats

    for idx, stat in enumerate(stats_to_plot):#EXCEPT counts, others are divided by the counts in the regions
        # get the raw data to plot as 2D array

        # if stat.startswith("count"):
        #     stat_array = stat_all[:,:,idx]
        # else: ## colocoalization
        #     old_err = np.seterr(all='ignore')##this may be the problem, by Ricky
        #     stat_array = stat_all[:,:,idx] /stat_all[:,:,1]
        #     #### set the stats_array of zero-counts regions to 0, by Ricky
        #     stat_array[np.where(stat_all[:,:,1] < 1)] = 0
        #     ###########################
        #     np.seterr(**old_err)
        #     # if idx == 2:
        #     # plt.imshow(stat_array)
        #     # plt.show()
        #     #     np.save("C:\\test.npy",stat_array)
        # # convert area to less horrible units (fakeinch^2 -> um^2)
        # # if stat == "area":
        # #     stat_array = stat_array * UM2_PER_Pixel2
        to_plot_stat = np.ones((stat_all.shape[0],stat_all.shape[1]))*np.nan
        stats_table[stat] = {}

        # mask in each region at a time
        # mask_proj = np.zeros([285,417])
        # qqq  = 0
        for mask_name in mask_set.images.keys():
            mask = mask_set.images[mask_name]
            # qqq = qqq + 1
            # mask out everything not in the region
            in_region = stat_array[(mask != 0) & np.isfinite(stat_array)]
            # get mean over boxes
            # mean_stat = np.mean(in_region)
            # print(mask_name)
            mean_stat = np.median(in_region)#try median by Ricky, 25/03/2014

            stats_table[stat][mask_name[:-4]] = mean_stat

            # save mean to summary
            #check the difference of mask_for_image and mask, by Ricky,
            # erosion a little bit to better display the boundaries between different regions of brain
            mask_for_image = ndimage.binary_erosion(mask)

            # mask_proj = mask_proj + mask_for_image
            if np.all(mask_for_image == 0):#if erode too much
                to_plot_stat[mask > 0] = mean_stat
            else:
                to_plot_stat[mask_for_image > 0] = mean_stat


        # plt.imshow(mask_proj)
        # plt.show()
        to_plot[:,:,idx] = to_plot_stat

    # ###plot the data, by Ricky
    # plt.subplot(2,1,1)
    # plt.imshow(mask)
    # plt.subplot(2,1,2)
    # plt.imshow(mask_for_image)
    # plt.show()
    # #######
    # # plt.colorbar(p0,ax=ax)

    out_dir = os.path.join(
        projects,
        tilepath.derived_root,
        instrument,
        mouse_folder_name,
        "stats"
    )

    # # save stats CSV
    # csv_filename = 'region_stats_table_'+filename_suffix+'.csv'
    # csv_path = os.path.join(out_dir,csv_filename)
    # csv_writer = csv.writer(open(csv_path,'wb'),dialect='excel-tab')
    # # rearrange our maps into tuples
    # csv_writer.writerow(["region"] + ["region"] + ["region"] + stats_to_plot_Jess) # first row is headers
    # for mask_name in mask_set.images.keys():
    #     csv_writer.writerow(
    #         [mask_name[:-4]] +
    #         [stats_table[stat][mask_name[:-4]] for stat in stats_to_plot_Jess]
    #     )

    ###########################################
    # save stats xls for Jess, by Ricky
    #####################
    xls_filename = 'region_stats_table_'+filename_suffix+'.xlsx'
    xls_path = os.path.join(out_dir,xls_filename)
    stats_dict_out = OrderedDict({"region":stats_table["mean"].keys()})
    for stat in stats_to_plot_Jess:
        stats_dict_out[stat] = stats_table[stat].values()
    # tttt = {stat:stats_table[stat].values() for stat in stats_to_plot_Jess}
    df = DataFrame(stats_dict_out)
    df.to_excel(xls_path,sheet_name='sheet1',index=False)
    # save stat image
    # stat_image_filename = 'region_stats_image_'+filename_suffix+'.npy'
    stat_image_filename_mat = 'region_stats_image_'+filename_suffix+'.mat'
    # npy_path = os.path.join(out_dir,stat_image_filename)
    mat_path = os.path.join(out_dir,stat_image_filename_mat)
    # np.save(npy_path,to_plot)
    # savemat(mat_path,{'region_stats':to_plot})


def do_counts_for_section_ZQ(
        select_mouse_path_root,
        channel_id,
        roi_subdirs
    ):#for Jess Data, by Ricky

    # scale = 2#for Jess Data
    section_name = select_mouse_path_root.split(os.sep)[-1]
    select_mouse_path = []
    for channel in channel_id:
        # temp_path_split = select_mouse_path.split(os.sep)#only valid for Olimpia data, by Ricky
        # select_mouse_path = os.sep.join(temp_path_split[:-1])#only valid for Olimpia data, by Ricky
        select_mouse_path.append(os.path.join(select_mouse_path_root,config.root_directory_output,channel))
    mask_dir = os.path.join(
            select_mouse_path[0],
            # select_mouse_path_root,config.root_directory_output,
            "masks",
            "scale_{0:03d}".format(config.scale)
    )
    mask_set = MaskSet(mask_dir)
    # load images, check they are in the desired set
    def in_roi_set(f):
        return any([f.startswith(s) for s in roi_subdirs])
    for mask_filename in os.listdir(mask_dir):#load mask images with name starting with 'main', by Rick Qiu 14/03/2014
        if in_roi_set(mask_filename) and mask_filename.endswith(config.Image_suffix):
           mask_set.load_image(mask_filename)
    make_region_stats_coloc(
                select_mouse_path,
                section_name,
                mask_set,
                list(channel_id),
                roi_subdirs,
            )

def make_region_stats_coloc(
                section_path_list,
                section_name,
                mask_set,
                channel_id,
                roi_sets,
                isflip ='N'#for Jess Data
):
    roi_set_description = ''.join(p for p in roi_sets)
                                  # if p != 'main')
    # mouse_id = mouse_folder_name.split("_")[1]#only valid for Jess data, need modification for other data!,by Ricky
    # section_id = mouse_folder_name.split("_")[-3]#only valid for Jess data, need modification for other data!,by Ricky
    # mouse_id,section_id,test_id = mouse_folder_name.split("_")
    # filename_suffix_list = {}
    # sums_filename_list = []
    stat_all_list = {}
    stats_table_list = {}
    to_plot_stat_list = {}
    stats_to_plot = [
        "counts", "coloc_all","coloc_channel","counts_all"]
    filename_suffix_list = {}
    # stats_to_plot_Jess = [
    #     "count_for_stats", "area", "mean"
    # ]
    stat_dir = {}
    for section_path in section_path_list:
        channel = section_path.split(os.sep)[-1]
        filename_suffix_noroi = "{}_distance{:3d}nm".format(section_name,coloc_threshold)
        filename_suffix_list[channel] = filename_suffix_noroi+"_"+roi_set_description#by Ricky
        sums_filename = 'stat_sums_'+filename_suffix_noroi+'.mat'
        stat_dir[channel] = os.path.join(section_path,"stats")
        stat_path = os.path.join(stat_dir[channel],sums_filename)
        stat_all_list[channel] = loadmat(stat_path)["sum_stats"]
        if isflip == "Y":
           stat_all_list[channel] = np.flipud(stat_all_list[channel])
    # create this as a dict of stat -> {region -> value} -- we'll save as CSV
        # to_plot = np.ones_like(stat_all_list[channel])*np.nan
    # density_SAP102 = stat_all_list[channel_id[0]][:,:,0]
    # density_PSD95 = stat_all_list[channel_id[0]][:,:,0]
    # density_coloc = stat_all_list["PSD95"][:,:,1]
    # stat_all_list[:,:,0] = density_coloc / density_SAP102
    # stat_all_list[:,:,1] = density_coloc / density_PSD95
    # stat_all_list["SAP102"][:,:,1] = density_percent
    # stat_all_list["PSD95"][:,:,1] = density_percent
    density_all =  stat_all_list[channel_id[0]][:,:,0] +  stat_all_list[channel_id[1]][:,:,0] \
                   - stat_all_list[channel_id[1]][:,:,1]
    density_percent = stat_all_list[channel_id[1]][:,:,1] / density_all
    density_percent[density_all == 0] = 0
    # for channel in channel_id:
    #     temp_coloc = stat_all_list[channel][:,:,1] / stat_all_list[channel][:,:,0]
    #     temp_coloc[stat_all_list[channel][:,:,0] == 0]  = 0
        # stat_all_list[channel][:,:,1] = density_percent
        # stat_all_list[channel] = np.dstack((stat_all_list[channel],temp_coloc))
    for section_path in section_path_list:
        stats_table = {}
        channel = section_path.split(os.sep)[-1]
        density_channel = stat_all_list[channel][:,:,0]
        # density_all = stats_all_list[channel][:,:,0]
        for idx, stat in enumerate(stats_to_plot):#EXCEPT counts, others are divided by the counts in the regions
            stats_table[stat] = {}
            # stat_array = stat_all_list[channel][:,:,idx]
            if stat.startswith('coloc_all'):
                density_coloc = stat_all_list[channel][:,:,1]
                for mask_name in mask_set.images.keys():
                    mask = mask_set.images[mask_name]
                    in_region_coloc = density_coloc[(mask != 0) & np.isfinite(density_coloc)]
                    in_region_density = density_all[(mask != 0) & np.isfinite(density_all)]
                    mean_stat = np.sum(in_region_coloc) / np.sum(in_region_density)
                    stats_table[stat][mask_name[:-4]] = mean_stat
            else:
                if stat.startswith('coloc_channel'):#colocalization per channel
                    density_coloc = stat_all_list[channel][:,:,1]
                    for mask_name in mask_set.images.keys():
                        mask = mask_set.images[mask_name]
                        in_region_coloc = density_coloc[(mask != 0) & np.isfinite(density_coloc)]
                        in_region_density = density_channel[(mask != 0) & np.isfinite(density_channel)]
                        mean_stat = np.sum(in_region_coloc) / np.sum(in_region_density)
                        stats_table[stat][mask_name[:-4]] = mean_stat
                else:#density
                    if stat.startswith("counts_all"):
                        for mask_name in mask_set.images.keys():
                            mask = mask_set.images[mask_name]
                            in_region = density_channel[(mask != 0) & np.isfinite(density_channel)]
                            sum_stat = np.sum(in_region)
                            stats_table[stat][mask_name[:-4]] = sum_stat
                    else:
                        for mask_name in mask_set.images.keys():
                            mask = mask_set.images[mask_name]
                            in_region = density_channel[(mask != 0) & np.isfinite(density_channel)]
                            mean_stat = np.median(in_region)
                            stats_table[stat][mask_name[:-4]] = mean_stat

        out_dir = stat_dir[channel]
        xls_filename = 'region_stats_table_'+filename_suffix_list[channel]+'.xlsx'
        xls_path = os.path.join(out_dir,xls_filename)
        stats_dict_out = OrderedDict({"region":stats_table["counts"].keys()})
        for stat in stats_to_plot:
            stats_dict_out[stat] = stats_table[stat].values()
    # tttt = {stat:stats_table[stat].values() for stat in stats_to_plot_Jess}
        df = DataFrame(stats_dict_out)
        df.to_excel(xls_path,sheet_name='sheet1',index=False)

    # # save stats CSV
    # csv_filename = 'region_stats_table_'+filename_suffix+'.csv'
    # csv_path = os.path.join(out_dir,csv_filename)
    # csv_writer = csv.writer(open(csv_path,'wb'),dialect='excel-tab')
    # # rearrange our maps into tuples
    # csv_writer.writerow(["region"] + ["region"] + ["region"] + stats_to_plot_Jess) # first row is headers
    # for mask_name in mask_set.images.keys():
    #     csv_writer.writerow(
    #         [mask_name[:-4]] +
    #         [stats_table[stat][mask_name[:-4]] for stat in stats_to_plot_Jess]
    #     )

    ###########################################
    # save stats xls for Jess, by Ricky
    #####################
    # save stat image
    # stat_image_filename = 'region_stats_image_'+filename_suffix+'.npy'
    # stat_image_filename_mat = 'region_stats_image_'+filename_suffix+'.mat'
    # # npy_path = os.path.join(out_dir,stat_image_filename)
    # mat_path = os.path.join(out_dir,stat_image_filename_mat)
    # np.save(npy_path,to_plot)
    # savemat(mat_path,{'region_stats':to_plot})
def do_counts_for_section_ZQ_density(
        select_mouse_path_root,
        channel_id,
        roi_subdirs
    ):#for Jess Data, by Ricky

    # scale = 2#for Jess Data
    section_name = select_mouse_path_root.split(os.sep)[-1]
    select_mouse_path = []
    for channel in channel_id:
        # temp_path_split = select_mouse_path.split(os.sep)#only valid for Olimpia data, by Ricky
        # select_mouse_path = os.sep.join(temp_path_split[:-1])#only valid for Olimpia data, by Ricky
        select_mouse_path.append(os.path.join(select_mouse_path_root,config.root_directory_output,channel))
    mask_dir = os.path.join(
            select_mouse_path[0],
            # select_mouse_path_root,config.root_directory_output,
            "masks",
            "scale_{0:03d}".format(config.scale)
    )
    mask_set = MaskSet(mask_dir)
    # load images, check they are in the desired set
    def in_roi_set(f):
        return any([f.startswith(s) for s in roi_subdirs])
    for mask_filename in os.listdir(mask_dir):#load mask images with name starting with 'main', by Rick Qiu 14/03/2014
        if in_roi_set(mask_filename) and mask_filename.endswith(config.Image_suffix):
           mask_set.load_image(mask_filename)
    make_region_stats(
                select_mouse_path,
                section_name,
                mask_set,
                list(channel_id),
                roi_subdirs,
            )

def make_region_stats(
                section_path_list,
                section_name,
                mask_set,
                channel_id,
                roi_sets,
                isflip ='N'#for Jess Data
):
    roi_set_description = ''.join(p for p in roi_sets)
                                  # if p != 'main')
    # mouse_id = mouse_folder_name.split("_")[1]#only valid for Jess data, need modification for other data!,by Ricky
    # section_id = mouse_folder_name.split("_")[-3]#only valid for Jess data, need modification for other data!,by Ricky
    # mouse_id,section_id,test_id = mouse_folder_name.split("_")
    # filename_suffix_list = {}
    # sums_filename_list = []
    stat_all_list = {}
    stats_table_list = {}
    to_plot_stat_list = {}
    stats_to_plot = [
        "counts", "counts_all"]
    filename_suffix_list = {}
    # stats_to_plot_Jess = [
    #     "count_for_stats", "area", "mean"
    # ]
    stat_dir = {}
    for section_path in section_path_list:
        channel = section_path.split(os.sep)[-1]
        # filename_suffix_noroi = "{}".format(section_name)
        filename_suffix_noroi = "{}_distance{:3d}nm".format(section_name,coloc_threshold)
        filename_suffix_list[channel] = filename_suffix_noroi+"_"+roi_set_description#by Ricky
        sums_filename = 'stat_sums_'+filename_suffix_noroi+'.mat'
        stat_dir[channel] = os.path.join(section_path,"stats")
        stat_path = os.path.join(stat_dir[channel],sums_filename)
        stat_all_list[channel] = loadmat(stat_path)["sum_stats"]
        if isflip == "Y":
           stat_all_list[channel] = np.flipud(stat_all_list[channel])
    # create this as a dict of stat -> {region -> value} -- we'll save as CSV
        # to_plot = np.ones_like(stat_all_list[channel])*np.nan
    # density_SAP102 = stat_all_list[channel_id[0]][:,:,0]
    # density_PSD95 = stat_all_list[channel_id[0]][:,:,0]
    # density_coloc = stat_all_list["PSD95"][:,:,1]
    # stat_all_list[:,:,0] = density_coloc / density_SAP102
    # stat_all_list[:,:,1] = density_coloc / density_PSD95
    # stat_all_list["SAP102"][:,:,1] = density_percent
    # stat_all_list["PSD95"][:,:,1] = density_percent
    # density_all =  stat_all_list[channel_id[0]][:,:,0] +  stat_all_list[channel_id[1]][:,:,0] \
    #                - stat_all_list[channel_id[1]][:,:,1]
    # density_percent = stat_all_list[channel_id[1]][:,:,1] / density_all
    # density_percent[density_all == 0] = 0
    # for channel in channel_id:
    #     temp_coloc = stat_all_list[channel][:,:,1] / stat_all_list[channel][:,:,0]
    #     temp_coloc[stat_all_list[channel][:,:,0] == 0]  = 0
        # stat_all_list[channel][:,:,1] = density_percent
        # stat_all_list[channel] = np.dstack((stat_all_list[channel],temp_coloc))
    for section_path in section_path_list:
        stats_table = {}
        channel = section_path.split(os.sep)[-1]
        density_channel = stat_all_list[channel][:,:,0]
        # density_all = stats_all_list[channel][:,:,0]
        for idx, stat in enumerate(stats_to_plot):#EXCEPT counts, others are divided by the counts in the regions
            stats_table[stat] = {}
            # stat_array = stat_all_list[channel][:,:,idx]
            # if stat.startswith('coloc_all'):
            #     density_coloc = stat_all_list[channel][:,:,1]
            #     for mask_name in mask_set.images.keys():
            #         mask = mask_set.images[mask_name]
            #         in_region_coloc = density_coloc[(mask != 0) & np.isfinite(density_coloc)]
            #         in_region_density = density_all[(mask != 0) & np.isfinite(density_all)]
            #         mean_stat = np.sum(in_region_coloc) / np.sum(in_region_density)
            #         stats_table[stat][mask_name[:-4]] = mean_stat
            # else:
            #     if stat.startswith('coloc_channel'):#colocalization per channel
            #         density_coloc = stat_all_list[channel][:,:,1]
            #         for mask_name in mask_set.images.keys():
            #             mask = mask_set.images[mask_name]
            #             in_region_coloc = density_coloc[(mask != 0) & np.isfinite(density_coloc)]
            #             in_region_density = density_channel[(mask != 0) & np.isfinite(density_channel)]
            #             mean_stat = np.sum(in_region_coloc) / np.sum(in_region_density)
            #             stats_table[stat][mask_name[:-4]] = mean_stat
            #     else:#density
            if stat.startswith("counts_all"):
                for mask_name in mask_set.images.keys():
                   mask = mask_set.images[mask_name]
                   in_region = density_channel[(mask != 0) & np.isfinite(density_channel)]
                   sum_stat = np.sum(in_region)
                   stats_table[stat][mask_name[:-4]] = sum_stat
                else:
                   for mask_name in mask_set.images.keys():
                       mask = mask_set.images[mask_name]
                       in_region = density_channel[(mask != 0) & np.isfinite(density_channel)]
                       mean_stat = np.median(in_region)
                       stats_table[stat][mask_name[:-4]] = mean_stat

        out_dir = stat_dir[channel]
        xls_filename = 'region_stats_table_'+filename_suffix_list[channel]+'.xlsx'
        xls_path = os.path.join(out_dir,xls_filename)
        stats_dict_out = OrderedDict({"region":stats_table["counts"].keys()})
        for stat in stats_to_plot:
            stats_dict_out[stat] = stats_table[stat].values()
    # tttt = {stat:stats_table[stat].values() for stat in stats_to_plot_Jess}
        df = DataFrame(stats_dict_out)
        df.to_excel(xls_path,sheet_name='sheet1',index=False)

    # # save stats CSV
    # csv_filename = 'region_stats_table_'+filename_suffix+'.csv'
    # csv_path = os.path.join(out_dir,csv_filename)
    # csv_writer = csv.writer(open(csv_path,'wb'),dialect='excel-tab')
    # # rearrange our maps into tuples
    # csv_writer.writerow(["region"] + ["region"] + ["region"] + stats_to_plot_Jess) # first row is headers
    # for mask_name in mask_set.images.keys():
    #     csv_writer.writerow(
    #         [mask_name[:-4]] +
    #         [stats_table[stat][mask_name[:-4]] for stat in stats_to_plot_Jess]
    #     )

    ###########################################
    # save stats xls for Jess, by Ricky
    #####################
    # save stat image
    # stat_image_filename = 'region_stats_image_'+filename_suffix+'.npy'
    # stat_image_filename_mat = 'region_stats_image_'+filename_suffix+'.mat'
    # # npy_path = os.path.join(out_dir,stat_image_filename)
    # mat_path = os.path.join(out_dir,stat_image_filename_mat)
    # np.save(npy_path,to_plot)
    # savemat(mat_path,{'region_stats':to_plot})

def do_counts_for_section_coloc(
        section_path_list,
        channel_params_list,
        projects_dir,
        roi_subdirs = ['main'],
        isflip = 'Y'
    ):
    # (projects_dir, instrument, sections, detection_method, channel_params,roi_subdirs,isflip):#for Jess Data, by Ricky

        #         do_counts_for_section_coloc(temp_section_path_list,channel_params_list,project_id)
        # projects,root_directory_raw,sections,OBJ_ID_STR[channel],channel_params, ['main'],isflip
    method_out_dict  = {}
    for channel, params in channel_params_list.iteritems():
        if channel == 'SAP102':
            method_out_dict[channel] = method_method_id_SAP102(OBJ_ID_STR[channel], params)
        else:
            method_out_dict[channel] = method_method_id(OBJ_ID_STR[channel], params)
    mask_dir = os.path.join(
            section_path_list[0],
            "masks",
            "scale_{0:03d}".format(config.scale)
        )
    mask_set = MaskSet(mask_dir)
    def in_roi_set(f):
        return any([f.startswith(s) for s in roi_subdirs])
    for mask_filename in os.listdir(mask_dir):#load mask images with name starting with 'main', by Rick Qiu 14/03/2014
        if in_roi_set(mask_filename):
           mask_set.load_image(mask_filename)
    make_region_stats_coloc(
        section_path_list,method_out_dict, channel_params_list, mask_set,roi_subdirs,isflip)#for Jess Data

    # mouse_folder_name = []
    # for section_path in section_path_list:
    #     mouse_folder_name.append(section_path.split(os.sep)[-1])

    # make_region_stats_ZQ(
    #             projects_dir,
    #             instrument,
    #             mouse_folder_name,
    #             channel,
    #             detection_method,
    #             params,
    #             mask_set,
    #             roi_subdirs,
    #             isflip
    #         )

    # channel, params = channel_params.items()[0]
    #
    # select_mouse_path_list =  config.projects_dir_for_section_ZQ(projects_dir,
    #                                                              os.path.join(config.root_directory_output,instrument),
    #                                                             sections,channel)#modified by Ricky
    # scale = 2#for Jess Data
    # for select_mouse_path in select_mouse_path_list:
        # temp_path_split = select_mouse_path.split(os.sep)#only valid for Olimpia data, by Ricky
        # select_mouse_path = os.sep.join(temp_path_split[:-1])#only valid for Olimpia data, by Ricky
        # mask_dir = os.path.join(
        #     select_mouse_path,
        #     "masks",
        #     "scale_{0:03d}".format(config.scale)
        # )
    # load images, check they are in the desired set
def do_histogram(
        select_mouse_path_root,
        channel_id,
        roi_subdirs,
        section_name

):
    metadata_path_list = glob(os.path.join(select_mouse_path_root,'*.txt'))#modified by Ricky
    raw_col_num,raw_row_num = util.extract_map_dim(metadata_path_list[0])
    # for channel in channel_id:
    channel_foldername  = config.channel_list[channel_id[0]]
    section_path = os.path.join(select_mouse_path_root,'distance_results',channel_foldername)
    zoom_factor = int(np.sqrt(len(config.XY_GRID)))
    obj_path = section_path
    sums = np.zeros((raw_row_num*zoom_factor,raw_col_num*zoom_factor,len(config.PARAMS_TO_GRID)))
    filename_suffix = "{section}_{channel1}to{channel2}_binsize{binsize}nm_range{binupper}nm".format(
                            section = section_name,
                            channel1 = channel_id[0],
                            channel2 = channel_id[1],
                            binsize = bin_size,
                            binupper = bin_upper
                            )
     # sums_filename_npy = 'stat_sums_'+filename_suffix+'.npy'
    hist_filename_csv = 'histogram_'+filename_suffix+'.csv'#by Ricky
    histogram_dir = os.path.join(select_mouse_path_root,config.root_directory_output,"histogram")#by Ricky
    util.makedirs_if_absent(histogram_dir)
    #====load mask files ===================================#
    mask_dir = os.path.join(
            select_mouse_path_root,config.root_directory_output,
            channel_id[0],
            "masks",
            "scale_{0:03d}".format(config.scale)
    )
    mask_set = MaskSet(mask_dir)
    # load images, check they are in the desired set
    def in_roi_set(f):
        return any([f.startswith(s) for s in roi_subdirs])
    for mask_filename in os.listdir(mask_dir):#load mask images with name starting with 'main', by Rick Qiu 14/03/2014
        if in_roi_set(mask_filename) and mask_filename.endswith(config.Image_suffix):
           mask_set.load_image(mask_filename)

##make bin for histogram  ###########
    bin_list = np.arange(0,bin_upper,bin_size)
        #   #===================start mapping ================================================================================>
    print("******************do histogram on {} *******************************".format(section_path))
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
    stats_table = {}
    stats_table["bins"] = bin_list[:-1]
    for mask_name in mask_set.images.keys():
        mask = mask_set.images[mask_name]
        count = 1
        distance_list = []
        histogram_list = []
        for i in range(0,raw_row_num):
            for j in range(0,raw_col_num):
                if mask[i,j] > 0:
                    temp_obj_filepath = os.path.join(obj_path,obj_files_list[new_order[count - 1]])
                    distance_list = collect_distance((temp_obj_filepath,distance_list))
                count += 1
        # [histogram_list,temp_bin] = np.histogram(np.array(distance_list),bins = 10,range = (0,bin_upper))
        distance_list = np.array(np.array(distance_list))
        [histogram_list,temp_bin] = np.histogram(distance_list,bins = bin_list,range = (0,bin_upper))
        # print(len(histogram_list))
        stats_table[mask_name[0:-4]] = histogram_list
    df = DataFrame(stats_table)
    df.to_csv(os.path.join(histogram_dir,hist_filename_csv),sep='\t')
    print('#==============time spent is {} seconds==================#'.format(time.time() - t))