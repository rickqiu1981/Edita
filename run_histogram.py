__author__ = 'ZQiu'
import sys
sys.path.append('..')
###############work flow of batch processing in g2c imaging###########################
############## by Ricky 02/09/2014#############################################
# import time
import config
import os
from stats_image_trackmate import make_stat_images_trackmate,make_stat_images_coloc
from region_masks import create_region_masks_ZQ
from stat_region_Ricky import do_counts_for_section_ZQ,do_histogram
# import datasets
# import detection_constants
# # from run_corsen_Ricky import main as corsen_main
# from run_stat_image_ZQ import main as stat_image_main
# import time
def main():
    project_id = "projectVlad"
    method_id = "trackmate"
################ developmental ############
    # # sections = [("PUP100","SG1","Y")]
    # sections = [("PUP120","SG2","N",3)]
    sections_list = [ "PUP068_1785_P21"]
    # sections_list = [
    #     # "CFS0049_sfinal",
    #     # "CFS0049",
    #     # "CFS0049"
    # ]
    for section in sections_list:
        select_mouse_path_root =  os.path.join(config.root_directory_raw,section)#modified by Ricky
        print("section  " + section)
        try:
        # create_region_masks_ZQ(select_mouse_path_root,config.channel_id,config.scale)##create mask files from ROI files
            do_histogram(select_mouse_path_root,config.channel_id,["main"],section)
        except OSError:
            print(select_mouse_path_root +" does not contain ROI zip files")

if __name__=='__main__':
    main()
