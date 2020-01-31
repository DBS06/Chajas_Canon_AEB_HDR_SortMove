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

    parser = create_parser()
    args = parser.parse_args()
    default_cfg_file_path = os.path.dirname(os.path.realpath(__file__)) + '/' + CDG_FILE_NAME
    config = load_json_cfg(default_cfg_file_path)

    print(args.path)
    if args.yes:
        print("auto yes")
    else:
        print("ask")

    print(config)


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
    main_parser.add_argument("-m", "--mode", action="store", default='auto',
                             help="defines if HDR-Search is based on exif-data, txt-files, or decide based on folders content: <auto/exif/txt>")
    main_parser.add_argument("-y", "--yes", action="store_true", default='',
                             help="sorting starts automatically, no asking!")

    return main_parser


if __name__ == "__main__":  # pragma: no cover
    main()
    sys.exit(0)
