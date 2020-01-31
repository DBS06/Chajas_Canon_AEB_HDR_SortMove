#!/usr/bin/python

from collections import deque
import argparse
import time
import json
import os
import string
import re
import shutil
import sys
import exifread

if sys.version_info < (3, 0):
    print("Sorry, Python 3.x is required")
    sys.exit(1)

#############################
# Globals
#############################

CDG_FILE_NAME = "config.json"
DEFAULT_STOP_TAG = ""

# placeholders for printing
print_img_plh = 13
print_tag_plh = 23

# Global Variables
searchDir = ""
image_file_ending = ""
imgFiles = []
hdr_move_list = deque()
hdr_skip_list = deque()
hdr_count = 0
hdr_list = []


class ExifTag(object):  # pylint: disable=too-few-public-methods
    """
    Class to define the EXIF-Tags which indicates that a picture is part of a HDR-Sequence
    """

    def __init__(self, name, val):
        # IFD name followed by the tag name. i.e.: 'EXIF DateTimeOriginal', 'Image Orientation', 'MakerNote FocusMode'
        self.name = name
        # value of the tag
        self.val = val


def main():  # pragma: no cover
    """
    parsing commandline args
    """

    print("####################################")
    print("# Chaja's - Canon AEB HDR SortMove #")
    print("####################################")

    parser = create_parser()
    args = parser.parse_args()

    if args.path == '':
        # Get path to image folder and proof if it exists
        while (1):
            directory = input("Path to Image Folder (abort with hit 'RETURN'): ")
            # directory = "C:\Users\phst\Pictures\Test_Pictures"
            if (directory == ""):
                sys.exit("Exit by User!")

            if (os.path.exists(directory)):
                searchDir = directory
                break
            else:
                print("invalid path!")
    else:
        if (os.path.exists(args.path)):
            searchDir = args.path
        else:
            sys.exit("invalid path!")

    print(searchDir)

    default_cfg_file_path = os.path.dirname(os.path.realpath(__file__)) + '/' + CDG_FILE_NAME
    config = load_json_cfg(default_cfg_file_path)

    # TODO: check which mode should be used
    parseGeneralCfg(config)

    # hdr_move_lise =
    getExifHdrList(config)


#############################
# Functions
#############################

def read_exif(path, exif_details, stop_tag=DEFAULT_STOP_TAG):
    img = open(path, 'rb')
    tags_img = exifread.process_file(img,  details=exif_details, stop_tag=stop_tag)
    img.close()
    return tags_img


def print_table():
    print("+-%s+-%s+-%s+-%s+" % ("-" * print_img_plh, "-" * print_tag_plh, "-" * print_tag_plh, "-" * print_tag_plh))
    return


def print_tags(img, tag1, tag2, tag3):
    print("| %-*s| %-*s| %-*s| %-*s|" % (print_img_plh, img, print_tag_plh, tag1, print_tag_plh, tag2, print_tag_plh, tag3))
    return


def load_json_cfg(json_cfg):
    ''' Remove comments from JSON cfg file and load the file '''
    with open(json_cfg, 'r') as config_file:
        config_without_comments = '\n'.join([row for row in config_file.readlines() if len(row.split('//')) == 1])
        return json.loads(config_without_comments, encoding="utf-8")


def create_parser():  # pragma: no cover
    """
    sets up the main commandline parser

    :return: parser object
    """
    main_parser = argparse.ArgumentParser(
        description='This script helps to sort HDR images from Canon Cameras')

    main_parser.add_argument("-p", "--path", action="store", default='', help="path to image folder")
    main_parser.add_argument("-m", "--mode", action="store", default='-',
                             help="defines if HDR-Search is based on exif-data, txt-files, or decide based on folders content: <auto/exif/txt>")
    main_parser.add_argument("-y", "--yes", action="store_true", default='',
                             help="sorting starts automatically, no asking!")

    return main_parser


def parseGeneralCfg(config):
    image_file_ending = config["general"]["imageSrcFileEnding"]


def getExifHdrList(config):
    # HDR-Sequence Stuff
    hdr_sequence_num_min = config["exifModeCfg"]["hdrSequenceMinNum"]

    # EXIF-Tags which indicates that a picture is part of a HDR-Sequence:
    # primary-tag is used to find the images which are part of an HDR-Sequence
    # this tag should be part of 'Standard'-EXIF-Tags to increase the search speed, otherwise it would be really slow
    exif_primary_tag = ExifTag(config["exifModeCfg"]["primaryTag"]["name"],
                               config["exifModeCfg"]["primaryTag"]["value"])

    # secondary- and tertiary-tag are used to find the beginning of a HDR-Sequence
    exif_secondary_tag = ExifTag(config["exifModeCfg"]["secondaryTag"]["name"],
                                 config["exifModeCfg"]["secondaryTag"]["value"])
    exif_tertiary_tag = ExifTag(config["exifModeCfg"]["tertiaryTag"]["name"],
                                config["exifModeCfg"]["tertiaryTag"]["value"])

    print("## EXIF-Mode")
    print("")
    print("## Settings:")
    print("# Primary EXIF-Tag:            " + exif_primary_tag.name + " -> Value: " + str(exif_primary_tag.val))
    print("# Secondary EXIF-Tag:          " + exif_secondary_tag.name + " -> Value: " + str(exif_secondary_tag.val))
    print("# Tertiary EXIF-Tag:           " + exif_tertiary_tag.name + " -> Value: " + str(exif_tertiary_tag.val))
    print("# Search Images:               *" + image_file_ending)
    print("# Min Images for HDR-Sequence: " + str(hdr_sequence_num_min))
    print("")


if __name__ == "__main__":  # pragma: no cover
    main()
    sys.exit(0)
