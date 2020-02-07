#!/usr/bin/python

from collections import deque
from dataclasses import dataclass
import argparse
import time
import json
import os
import string
import re
import shutil
import sys
import exifread
import fnmatch

if sys.version_info < (3, 0):
    print("Sorry, Python 3.x is required")
    sys.exit(1)

#############################
# Globals
#############################

CDG_FILE_NAME = "config.json"
DEFAULT_STOP_TAG = ""


@dataclass
class CfgGeneral:
    hdrMainDir_Prefix: str
    hdrMainDir_Postfix: str
    hdrMainDir_useParentFolderName: bool
    hdrMainDir_CustomName: str

    hdrSubDir_Prefix: str
    hdrSubDir_Postfix: str
    hdrSubDir_useParentFolderName: bool
    hdrSubDir_CustomName: str
    hdrSubDir_numPadding: int

    imageSrcFileEnding: str
    previewFiles_create: bool
    previewFiles_convertRawToJpg: bool
    previewFiles_convertQuality: str

    createLogFile: bool


@dataclass
class CfgExifMode:
    primaryTag_name: str
    primaryTag_value: str
    secondaryTag_name: str
    secondaryTag_value: str
    tertiaryTag_name: str
    tertiaryTag_value: str
    hdrSequenceMinNum: int


@dataclass
class CfgTxtMode:
    fileNameFilter: str
    fileEnding: str
    deleteTxtFiles: bool


@dataclass
class GeneralData:
    searchDirName = ""
    searchDirPath = ""
    targetMainDirName = ""
    targetMainDirPath = ""
    targetSubDirNameMask = ""
    imgFiles = []
    hdrMoveList = deque()
    hdrSkipList = deque()
    hdrCount = 0
    hdrCountOffset = 0
    hdrList = []


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

    print("####################################")
    print("# Chaja's - Canon AEB HDR SortMove #")
    print("####################################")

    parser = createParser()
    args = parser.parse_args()
    genData = GeneralData()

    defaultCfgFilePath = os.path.dirname(os.path.realpath(__file__)) + '/' + CDG_FILE_NAME
    config = loadJsonCfg(defaultCfgFilePath)

    cfgGeneral = parseGeneralCfg(config)
    cfgExif = parseExifModeCfg(config)
    cfgTxt = parseTxtModeCfg(config)

    if args.path == '':
        # Get path to image folder and proof if it exists
        while (1):
            directory = input("Path to Image Folder (abort with hit 'RETURN'): ")
            # directory = "C:\Users\phst\Pictures\Test_Pictures"
            if (directory == ""):
                sys.exit("Exit by User!")

            if (os.path.exists(directory)):
                genData.searchDir = directory
                break
            else:
                print("invalid path!")
    else:
        if (os.path.exists(args.path)):
            genData.searchDir = args.path
        else:
            sys.exit("invalid path!")

    # Fill up general data
    genData.searchDirPath = os.path.basename(genData.searchDir)
    if (cfgGeneral.hdrMainDir_useParentFolderName):
        genData.targetMainDirName = cfgGeneral.hdrMainDir_Prefix + genData.searchDirPath + cfgGeneral.hdrMainDir_Postfix
    else:
        genData.targetMainDirName = cfgGeneral.hdrMainDir_Prefix + \
            cfgGeneral.hdrMainDir_CustomName + cfgGeneral.hdrMainDir_Postfix

    genData.targetMainDirPath = os.path.join(genData.searchDir, genData.targetMainDirName)

    if (cfgGeneral.hdrMainDir_useParentFolderName):
        genData.targetSubDirNameMask = cfgGeneral.hdrSubDir_Prefix + genData.searchDirPath + cfgGeneral.hdrSubDir_Postfix
    else:
        genData.targetSubDirNameMask = cfgGeneral.hdrSubDir_Prefix + \
            cfgGeneral.hdrSubDir_CustomName + cfgGeneral.hdrSubDir_Postfix

    if os.path.exists(genData.targetMainDirPath):
        print("prexisting folder '" + genData.targetMainDirPath + "' found!")
        existingHdrFolders = fnmatch.filter(os.listdir(genData.targetMainDirPath), genData.targetSubDirNameMask + '*')
        if (len(existingHdrFolders) > 0):
            genData.hdrCountOffset = 0
            for folder in existingHdrFolders:
                folderNum = int(folder.replace(genData.targetSubDirNameMask, ''))
                if (folderNum > genData.hdrCountOffset):
                    genData.hdrCountOffset = folderNum

    print("General Data:")
    print(genData.searchDirName)
    print(genData.searchDirPath)
    print(genData.targetMainDirName)
    print(genData.targetMainDirPath)
    print(genData.targetSubDirNameMask)
    print(str(genData.hdrCountOffset))

    # TODO: check which mode should be used
    # hdr_move_list =
    getExifHdrList(genData, cfgGeneral, cfgExif)


#############################
# Functions
#############################

def readExif(path, exif_details, stop_tag=DEFAULT_STOP_TAG):
    img = open(path, 'rb')
    tags_img = exifread.process_file(img, details=exif_details, stop_tag=stop_tag)
    img.close()
    return tags_img


def printTable():
    print("+-%s+-%s+-%s+-%s+" % ("-" * print_img_plh, "-" * print_tag_plh, "-" * print_tag_plh, "-" * print_tag_plh))
    return


def printTags(img, tag1, tag2, tag3):
    print("| %-*s| %-*s| %-*s| %-*s|" % (print_img_plh, img, print_tag_plh, tag1, print_tag_plh, tag2, print_tag_plh, tag3))
    return


def loadJsonCfg(json_cfg):
    ''' Remove comments from JSON cfg file and load the file '''
    with open(json_cfg, 'r') as config_file:
        config_without_comments = '\n'.join([row for row in config_file.readlines() if len(row.split('//')) == 1])
        return json.loads(config_without_comments, encoding="utf-8")


def createParser():  # pragma: no cover
    """
    sets up the main commandline parser

    :return: parser object
    """
    mainParser = argparse.ArgumentParser(
        description='This script helps to sort HDR images from Canon Cameras')

    mainParser.add_argument("-p", "--path", action="store", default='', help="path to image folder")
    mainParser.add_argument("-m", "--mode", action="store", default='-',
                            help="defines if HDR-Search is based on exif-data, txt-files, or decide based on folders content: <auto/exif/txt>")
    mainParser.add_argument("-y", "--yes", action="store_true", default='',
                            help="sorting starts automatically, no asking!")

    return mainParser


def parseGeneralCfg(config):
    return CfgGeneral(config["general"]["hdrMainDir"]["Prefix"],
                      config["general"]["hdrMainDir"]["Postfix"],
                      config["general"]["hdrMainDir"]["Name"]["useParentFolderName"],
                      config["general"]["hdrMainDir"]["Name"]["CustomName"],
                      config["general"]["hdrSubDir"]["Prefix"],
                      config["general"]["hdrSubDir"]["Postfix"],
                      config["general"]["hdrSubDir"]["Name"]["useParentFolderName"],
                      config["general"]["hdrSubDir"]["Name"]["CustomName"],
                      config["general"]["hdrSubDir"]["numPadding"],
                      config["general"]["imageSrcFileEnding"],
                      config["general"]["previewFiles"]["create"],
                      config["general"]["previewFiles"]["convertRawToJpg"],
                      config["general"]["previewFiles"]["convertQuality"],
                      config["general"]["createLogFile"])


def parseExifModeCfg(config):
    return CfgExifMode(config["exifModeCfg"]["primaryTag"]["name"],
                       config["exifModeCfg"]["primaryTag"]["value"],
                       config["exifModeCfg"]["secondaryTag"]["name"],
                       config["exifModeCfg"]["secondaryTag"]["value"],
                       config["exifModeCfg"]["tertiaryTag"]["name"],
                       config["exifModeCfg"]["tertiaryTag"]["value"],
                       config["exifModeCfg"]["hdrSequenceMinNum"])


def parseTxtModeCfg(config):
    return CfgTxtMode(config["txtModeCfg"]["fileNameFilter"],
                      config["txtModeCfg"]["fileEnding"],
                      config["txtModeCfg"]["deleteTxtFiles"])


def getExifHdrList(genData, cfgGeneral, cfgExif):
    print("## EXIF-Mode")
    print("")
    print("## Settings:")
    print("# Primary EXIF-Tag:            " + cfgExif.primaryTag_name + " -> Value: " + cfgExif.primaryTag_value)
    print("# Secondary EXIF-Tag:          " + cfgExif.secondaryTag_name + " -> Value: " + cfgExif.secondaryTag_value)
    print("# Tertiary EXIF-Tag:           " + cfgExif.tertiaryTag_name + " -> Value: " + cfgExif.tertiaryTag_value)
    print("# Search Images:               *" + cfgGeneral.imageSrcFileEnding)
    print("# Min Images for HDR-Sequence: " + str(cfgExif.hdrSequenceMinNum))
    print("")


if __name__ == "__main__":  # pragma: no cover
    main()
    sys.exit(0)
