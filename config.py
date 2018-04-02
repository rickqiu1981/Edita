'''

@modified by Ricky 16/07/2014
'''
from multiprocessing import cpu_count
import os
import sys
#############directory path
import platform
osname = platform.system()
if osname == 'Windows':#for windows
    projects_dir = {

        'projectVlad':'C:\GKD_project', #config
        'projectCarlos':os.path.join('Z:','microscopy','2017-01_PSD95_SAP102_Pax6_Mapping'),
        "projectEdita":os.path.join('Z:','microscopy','02_2018_SiRHalo_TMR_PSD95Halo'),
    }
    ij_config = {
##############################################################
    # for work station, by Ricky 30/04/2014
    # 'java':'/data/software/Fiji.app/java/linux-amd64/jdk1.6.0_24/jre/bin/java',
        'puncta_src': '.\macros\dist',
        'plugins_dir': '.\macros\dist',#'/home/atullo2/g2cimaging/puncta/java/src/org/genes2cognition/ijplugin',
    }
    TEMP_DIR = os.path.join('C:','Users','s1692047','AppData','Local','Temp')#replace <username> with your own username
    # root_directory_raw = os.path.join('Z:','users','Vlad','microscopy','SDM','Selector GKD')
    root_directory_raw = os.path.join('Z:','microscopy','02_2018_SiRHalo_TMR_PSD95Halo')
    root_directory_output = os.path.join('Z:',"microscopy","imaging_derived","02_2018_SiRHalo_TMR_PSD95Halo")
else:#for linux
    projects_dir = {
        'projectVlad':'/remote/project3/users/Vlad/microscopy/SDM', #config
        'projectCarlos':os.path.join('/remote','project3','microscopy','2017-01_PSD95_SAP102_Pax6_Mapping'),
        "projectEdita":os.path.join('/remote','project3','microscopy','02_2018_SiRHalo_TMR_PSD95Halo'),

    }
    ij_config = {
##############################################################
    # for work station, by Ricky 30/04/2014
    # 'java':'/data/software/Fiji.app/java/linux-amd64/jdk1.6.0_24/jre/bin/java',
        'puncta_src': './macros/dist',
        'plugins_dir': './macros/dist',#'/home/atullo2/g2cimaging/puncta/java/src/org/genes2cognition/ijplugin',
    }
    TEMP_DIR = "/run/shm"#replace <username> with your own username
    root_directory_raw = os.path.join('/remote','project3','microscopy','02_2018_SiRHalo_TMR_PSD95Halo')
    root_directory_output = os.path.join('/remote','project3',"microscopy","imaging_derived","02_2018_SiRHalo_TMR_PSD95Halo")

    # root_directory_raw = os.path.join('/remote','project3','microscopy','2017-01_PSD95_SAP102_Pax6_Mapping','Hom')

n_processes = cpu_count()
# chunksize = cpu_count()/n_processes
chunksize = 1
# root_directory_output = "imaging_derived"
TILE_SIZE = 512
BOX_SIZE = 512
scale = TILE_SIZE / BOX_SIZE
GRID = range(0,TILE_SIZE,BOX_SIZE)
XY_GRID = [(x,y) for x in GRID for y in GRID]
PARAMS_TO_GRID = [
    "count"
]
PARAMS_COLOC = ["count_for_stats","coloc"]
Image_suffix = 'tif'
scale = 1
channel_id = ['PSD95'
    # ,'SAP102'
              ]
channel_list = {
    channel_id[0]:"c1",#folder name for the distance results
    # channel_id[1]:"c2"#folder name for the distance results
}