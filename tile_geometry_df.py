__author__ = 'atullo2'

import pprint

import numpy as np

def tile_geometry(df,tile_size_um,thumb_size_px):
    assert("x_um" in df)
    assert("y_um" in df)

    g = dict()
    g["thumb_size_px"] = thumb_size_px
    g["tile_size_um"] = tile_size_um
    g["thumb_px_per_um"] = float(thumb_size_px) / float(tile_size_um)
    g["max_x"] = np.max(df["x_um"])
    g["min_x"] = np.min(df["x_um"])
    g["max_y"] = np.max(df["y_um"])
    g["min_y"] = np.min(df["y_um"])
    # now canvas will be from (min_x,max_x+tile) and from (min_y, max_y+tile)
    g["canvas_x"] = int(np.ceil((g["max_x"]-g["min_x"])*g["thumb_px_per_um"]+g["thumb_size_px"]))
    g["canvas_y"] = int(np.ceil((g["max_y"]-g["min_y"])*g["thumb_px_per_um"]+g["thumb_size_px"]))
    g["x_offset"] = -g["min_x"]
    g["y_offset"] = -g["min_y"]
    return g

def convert_to_image_space(df,g):
    df["image_x"] = (df["x_um"] + g["x_offset"])*g["thumb_px_per_um"]
    df["image_y"] = g["canvas_y"]-(df["y_um"] + g["y_offset"])*g["thumb_px_per_um"]-g["thumb_size_px"]
