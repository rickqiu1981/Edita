
# old dataset structure

import config
import os
import pprint
import re
import sys

mapping_base = {
    'projects': 'Imaging/From CV1000/Mapping Scan/Mapping1_PSD95_SAP102',
    'projTNiK': 'Imaging/From CV1000/Mapping Scan/Mapping_PSD95_TNiK-KO',
    # 'proj2m1': 'Synaptic_Mapping_From_CV1000/Mapping1_PSD95_SAP102',//by Ricky, test
    'proj2m2': 'Synaptic_Mapping_From_CV1000/Mapping2_PSD95_PSD93',
    'proj2m3': 'Synaptic_Mapping_From_CV1000/Mapping3_PSD95',
    'proj2m4': 'Synaptic_Mapping_From_CV1000/Mapping4_PSD95_Dbn1KO',
    'proj2m5': 'Synaptic_Mapping_From_CV1000/Mapping5_PSD95_SAP102_dblHomo',
    'proj2m6': 'Synaptic_Mapping_From_CV1000/Mapping6_PSD95_PSD93KO',
    'projects2av': 'Arc_Venus_Mapping_CV1000/2013_11_KA_mapping_corsen',
    'projectRicky':'Synaptic_Mapping_From_CV1000/Mapping1_PSD95_SAP102'
}

arcvenus = [
    ('AVHomo11', 999),
    ('AVHomo07', 999)
]

arcvenus2 = [
    ('AVM11', 1),
    ('AVM22', 2),
    ('AVM3', 3),
    ('AVM5', 4),
    ('AVM22', 5),
    ('AVM7', 6),
    ('AVM63', 7),
    ('AVM7', 8),
]

datasets = dict()

#1- Sept13        no222 (hia
#2- Oct1             no151 (striatum)
#3- Oct4             no91 (olfactory bulbs)
#4- Oct8             no369 (cerebellum)
#5- Oct10           no279 (banana)
#6- Oct17           no224 (hippocampus)
#7- Oct24           no87 (olfactory bulbs)
#8- Oct30           no148 (striatum) 

# section number, scan name in base, volume id (projects or projects2)

datasets['base'] = {
    #('AVHomo11', 999): ('2013-04-10_Arc-venus_1hr_KA_hippocampus_cortex', 'projects2av'),
    #('AVHomo07', 999): ('2013-04-11_Arc-venus_2hr_KA_hippocampus_cortex', 'projects2av'),
    ('AVM11', 1): ('2013_05_06_AV_M11_1hr_KA_hippocampus', 'projects2av'),
    ('AVM22', 2): ('2013_05_06_AV_M22_6hr_KA_hippocampus_section1', 'projects2av'),
    ('AVM3', 3): ('2013_05_06_AV_M3_HC_KA_hippocampus', 'projects2av'),
    ('AVM5', 4): ('2013_05_06_AV_M5_30min_KA_hippocampus', 'projects2av'),
    ('AVM22', 5): ('2013_05_07_AV_M22_6hr_KA_hippocampus_section2', 'projects2av'),
    ('AVM7', 6): ('2013_05_07_AV_M7_2hr_KA_hippocampus', 'projects2av'),
    ('AVM63', 7): ('2013_05_07_M63_WT_hippocampus', 'projects2av'),
    ('AVM7', 8): ('2013-05-10_AV_M7_2hr_KA_x10_whole_coronal', 'projects2av'),
    ('GFR257', 1): ('2013-06-11_GFR257','proj2m3'),


}

datasets['base'] = {
    k : (mapping_base[v[1]]+'/'+v[0]+'/',v[1])
    # k : (mapping_base[v[1]]+v[0],v[1])
    for (k,v) in datasets['base'].iteritems()
}

def match_section_dir(dirname):
    mouse_re = r'_([A-Z]{3}\d{3})_'
    section_re = r'_Section(\d{3})_'
    mouse_match = re.search(mouse_re,dirname)
    section_match = re.search(section_re,dirname)
    if mouse_match is not None and section_match is not None:
        return mouse_match.group(1), int(section_match.group(1))
    else:
        return None

def get_datasets(searchpath_rel,searchpath_id):
    result = {}
    # make this into an absolute path per config
    projects = config.projects_dir[searchpath_id]
    searchpath_abs = os.path.join(projects, searchpath_rel)
    max_depth = 2 # max depth *from root*
    root_depth = searchpath_abs.count(os.path.sep)
    for root, dirs, files in os.walk(searchpath_abs,topdown=True):
        if 'G2C_supp_data' in root:
            dirs[:] = []
            continue
        if root.count(os.path.sep) - root_depth > max_depth:
            dirs[:] = [] # don't go any further
            continue
        # if this dir contains any dataset dirs, we can prune
        contains_datasets = False
        for dataset_dir in dirs:
            section_path = os.path.join(root,dataset_dir)
            mouse_section = match_section_dir(dataset_dir)
            if mouse_section is not None:
                # trim projects
                section_path = section_path[len(projects):].lstrip(os.path.sep)
                result[mouse_section] = (section_path, searchpath_id)
            contains_datasets = True

        if contains_datasets:
            dirs[:] = []

    return result

for k, v in mapping_base.items():
   datasets['base'].update(get_datasets(v,k))

def all_sections(mouse):
    return [k for k in datasets['base'].keys() if k[0] == mouse]

datasets['dirs'] = {
# section 1
('GKD017', 222) :
( '20120913T102410_scan1',
  '20120913T122458_scan2',
  '20120913T141400_scan3',
  '20120913T194207_scan4',
  '20120913T203721_scan5',
  '20120914T085839_scan6',
  '20120914T151221_scan7',
  '20120914T185328_scan8',
  '20120915T091905_scan9',
  '20120915T163504_scan10'),
# section 2
('GKD017', 151) :
(  '20121001T110814_scan1',
  '20121001T115452_scan2',
  '20121001T130935_scan3',
  '20121001T171123_scan4_5',
  '20121002T062635_scan6',
  '20121002T065742_scan7',
  '20121002T091555_scan8',
  '20121002T120908_scan9',
  '20121002T151913_scan10',
  '20121002T155948_scan11',
  '20121002T185728_scan12_13_14_15',
  '20121003T083733_scan14_15',
  '20121003T142321_scan16',
  '20121003T165725_scan17',
  '20121003T184647_scan18'),
# section 3
('GKD017', 91 ) :
(  '20121004T113246_scan1',
  '20121004T124832_scan2',
  '20121004T143104_scan3',
  '20121004T155407_scan4',
  '20121004T200152_scan5678',
  '20121005T092908_scan9',
  '20121005T113057_scan10',
  '20121005T162405_scan1112'),
# section 4
('GKD017', 369) :
( '20121008T131546_scan1',
  '20121008T171741_scan2345',
  '20121009T100910_scan6',
  '20121009T161350_scan7',
  '20121009T201001_scan891011'),
# section 5
('GKD017', 279) :
( '20121010T204812_scan123',
  '20121011T105921_scan4',
  '20121011T175147_scan567',
  '20121012T110705_scan8',
  '20121012T182845_scan9101112'),
# section 6
('GKD017', 224) :
( '20121017T135320_scan1',
  '20121017T192609_scan2',
  '20121018T125351_scan3',
  '20121018T132956_scan4',
  '20121018T192038_scan56',
  '20121019T105842_scan7',
  '20121019T125611_scan8',
  '20121019T163425_scan9',
  '20121019T170928_scan101112',
  '20121020T110940_scan13'),
# section 7
('GKD017', 87 ) :
( '20121024T143431_scan1',
  '20121024T161433_scan2',
  '20121024T201904_scan34567',
  '20121025T101500_scan8',
  '20121025T144210_scan910'),
# section 8
('GKD017', 148) :
( '20121030T164738_scan1',
  '20121030T191318_scan2_3_4_5',
  '20121031T104105_scan6',
  '20121031T143906_scan7_8',
  '20121031T165530_scan9_10_11_12_13',
  '20121101T112228_scan14'),
('GKD017', 89 ) :
( '20121128T183039_scan1234',
  '20121129T121825_scan56',
  '20121129T154039_scan78',
  '20121129T181159_scan91011'),
('GKD061', 176) :
( '20121211T192818_scan1-5',
  '20121212T124800_scan6-11'),
('GKD061', 332) :
( '20121213T135357_scan1',
  '20121213T141156_scan2',
  '20121213T171617_scan3-8',
  '20121214T085229_scan9-13',
  '20121214T133702_scan14',
  '20121214T162906_scan15',
  '20121214T183545_scan16-23'),
('GKD061', 529) :
( '20121217T110507_scan1',
  '20121217T115753_scan2',
  '20121217T145716_scan3',
  '20121217T184510_scan4-6',
  '20121218T104943_scan7-9',
  '20121218T172741_scan10',
  '20121218T192322_scan11'
),
('GKD061', 229) :
( '20121220T104300_scan1',
  '20121220T110636_scan2',
  '20121220T112734_scan3',
  '20121220T133504_scan4',
  '20121220T144139_scan5',
  '20121220T174730_scan6',
  '20121220T200205_scan7-12',
  '20121221T120729_scan13-18'),
('GKD061', 226) :
( '20130116T124723_scan1',
  '20130116T143512_scan2',
  '20130116T171900_scan3',
  '20130116T195115_scan4-7',
  '20130117T093409_scan8',
  '20130117T120820_scan9-10',
  '20130117T133837_scan11',
  '20130117T153127_scan12',
  '20130117T172043_scan13-14'),
('GKD061', 387) :
( '20130110T101939_scan1',
  '20130110T115348_scan2',
  '20130110T142428_scan3',
  '20130110T170145_scan4',
  '20130110T184839_scan5-10',
  '20130111T102241_scan11',
  '20130111T152232_scan12-13',
  '20130111T181104_scan14-22'),
('GKD061', 334) :
( '20130121T134355_scan1',
  '20130121T163008_scan2',
  '20130121T190745_scan3-6',
  '20130122T100211_scan7-8',
  '20130122T141215_scan9-10',
  '20130122T181811_scan11-13',
  '20130123T105757_scan14-16'),
('GKD061', 185) :
( '20130125T102348_scan1',
  '20130125T123349_scan2',
  '20130125T151428_scan3',
  '20130125T181009_scan4-7',
  '20130126T111802_scan8'),
('GKD061', 520) :
( '20130128T124230_scan1',
  '20130128T131602_scan2-3',
  '20130128T153147_scan4-6',
  '20130128T184349_scan7-9',
  '20130129T093712_scan10-11',
  '20130129T141003_scan12-13'),
('AVHomo11',999) :
( '20130410T184700',),
('AVHomo07',999) :
( '20130411T125251',)
}

