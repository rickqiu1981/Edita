__author__ = 'atullo2'

import cPickle
import os

import pandas as pd

import config
import datasets
import tilepath

ds = datasets.datasets

SECTION_METADATA_FILENAME = "section_pos_info.pkl"

class SectionMetadata():
    def __init__(self,instrument,mouse,section,tile_info):
        """
        Position info for a section -- does not say anything about
        available root, method, channel or stacklevel
        :param instrument: instrument ID
        :param mouse: mouse ID
        :param section: section ID (int)
        :param tile_info: iter over tuples
            (imagedir,tile number,x,y)
        :return: new instance
        """
        self.instrument = instrument
        self.mouse = mouse
        self.section = section
        self.tiles = pd.DataFrame(
            tile_info,
            columns=["imagedir","tile_number","x_um","y_um","order_hint"]
        )

    def __eq__(self, other):
        return (
            self.tiles.shape == other.tiles.shape and
            self.instrument == other.instrument and
            self.mouse == other.mouse and
            self.section == other.section and
            pd.merge(self.tiles,other.tiles).shape == self.tiles.shape
        )

    def save(self,filename):
        f = open(filename,"wb")
        cPickle.dump(self,f,protocol=2)

    @staticmethod
    def load(filename):
        f = open(filename,"rb")
        result = cPickle.load(f)
        assert(isinstance(result,SectionMetadata))
        return result


def section_metadata_path(instrument,mouse_id,section_id):
    projects = config.projects_dir_for_section(ds,(mouse_id,section_id))
    return os.path.join(
        projects,tilepath.captured_root,instrument,
        tilepath.mouse_dirname(mouse_id),
        tilepath.section_dirname(section_id),
        SECTION_METADATA_FILENAME
    )

def section_metadata(instrument,mouse_id,section_id):
    metadata_path = section_metadata_path(instrument,mouse_id,section_id)
    print(metadata_path)
    return SectionMetadata.load(metadata_path)
