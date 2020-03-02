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
'''
from PIL import Image
import io
'''

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
    hdrSequenceMinNum: int
    previewFiles_create: bool
    previewFiles_convertRawToJpg: bool
    previewFiles_convertQuality: str

    createLogFile: bool


@dataclass
class CfgExifMode:
    enable: bool
    primaryTag_name: str
    primaryTag_value: str
    secondaryTag_name: str
    secondaryTag_value: str
    tertiaryTag_name: str
    tertiaryTag_value: str


@dataclass
class CfgTxtMode:
    enable: bool
    fileNameFilter: str
    fileEnding: str


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
                genData.searchDirPath = directory
                break
            else:
                print("invalid path!")
    else:
        if (os.path.exists(args.path)):
            genData.searchDirPath = args.path
        else:
            sys.exit("invalid path!")

    # Fill up general data
    genData.searchDir = os.path.basename(genData.searchDirPath)
    if (cfgGeneral.hdrMainDir_useParentFolderName):
        genData.targetMainDirName = cfgGeneral.hdrMainDir_Prefix + genData.searchDir + cfgGeneral.hdrMainDir_Postfix
    else:
        genData.targetMainDirName = cfgGeneral.hdrMainDir_Prefix + \
            cfgGeneral.hdrMainDir_CustomName + cfgGeneral.hdrMainDir_Postfix

    genData.targetMainDirPath = os.path.join(genData.searchDirPath, genData.targetMainDirName)

    if (cfgGeneral.hdrMainDir_useParentFolderName):
        genData.targetSubDirNameMask = cfgGeneral.hdrSubDir_Prefix + genData.searchDir + cfgGeneral.hdrSubDir_Postfix
    else:
        genData.targetSubDirNameMask = cfgGeneral.hdrSubDir_Prefix + \
            cfgGeneral.hdrSubDir_CustomName + cfgGeneral.hdrSubDir_Postfix

    for i in range(2):
        # Check if a previous HDR-Move was done and extract the highest HDR-Number
        if os.path.exists(genData.targetMainDirPath):
            print("prexisting folder '" + genData.targetMainDirPath + "' found!")
            existingHdrFolders = fnmatch.filter(os.listdir(genData.targetMainDirPath),
                                                genData.targetSubDirNameMask + '*')
            if (len(existingHdrFolders) > 0):
                genData.hdrCountOffset = 0
                for folder in existingHdrFolders:
                    folderNum = int(folder.replace(genData.targetSubDirNameMask, ''))
                    if (folderNum > genData.hdrCountOffset):
                        genData.hdrCountOffset = folderNum

        print("General Data:")
        print("searchDirName:        " + genData.searchDirName)
        print("searchDir:            " + genData.searchDir)
        print("searchDirPath:        " + genData.searchDirPath)
        print("targetMainDirName:    " + genData.targetMainDirName)
        print("targetMainDirPath:    " + genData.targetMainDirPath)
        print("targetSubDirNameMask: " + genData.targetSubDirNameMask)
        print("hdrCountOffset:       " + str(genData.hdrCountOffset))
        print("####################################")
        print("")

        if i == 0 and cfgTxt.enable:
            getTxtHdrList(genData, cfgGeneral, cfgTxt)
        elif i == 1 and cfgExif.enable:
            getExifHdrList(genData, cfgGeneral, cfgExif)
        else:
            continue

        if len(genData.hdrMoveList) == 0:
            print("No HDRs found in this directory!")
            continue

        print("\r\nHDRs Found: %d" % (len(genData.hdrMoveList)))

        if (args.yes is False):
            # Ask user if he wants to proceed
            proceed = input("Do you want to start the moving the found HDR-Sequences? (Y)es (N)o: ")
            if ((proceed is "Y") or (proceed is "y")):
                print("Start copying...")
            else:
                sys.exit("Exit by User!")
        else:
            print("Auto proceed selected!")
            print("Start copying...")

        copyHdrList(genData, cfgGeneral)

        genData.imgFiles.clear()
        genData.hdrMoveList.clear()
        genData.hdrSkipList.clear()
        genData.hdrCount = 0
        genData.hdrCountOffset = 0
        genData.hdrList.clear()


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


def printSmallTable():
    print("+-%s+" % ("-" * print_img_plh))
    return


def printSmallTags(img):
    print("| %-*s|" % (print_img_plh, img))
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
    mainParser.add_argument("-y", "--yes", action="store_true", default=False,
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
                      "." + config["general"]["imageSrcFileEnding"],
                      config["general"]["hdrSequenceMinNum"],
                      config["general"]["previewFiles"]["create"],
                      config["general"]["previewFiles"]["convertRawToJpg"],
                      config["general"]["previewFiles"]["convertQuality"],
                      config["general"]["createLogFile"])


def parseExifModeCfg(config):
    return CfgExifMode(config["exifModeCfg"]["enable"],
                       config["exifModeCfg"]["primaryTag"]["name"],
                       config["exifModeCfg"]["primaryTag"]["value"],
                       config["exifModeCfg"]["secondaryTag"]["name"],
                       config["exifModeCfg"]["secondaryTag"]["value"],
                       config["exifModeCfg"]["tertiaryTag"]["name"],
                       config["exifModeCfg"]["tertiaryTag"]["value"])


def parseTxtModeCfg(config):
    return CfgTxtMode(config["txtModeCfg"]["enable"],
                      config["txtModeCfg"]["fileNameFilter"],
                      config["txtModeCfg"]["fileEnding"])


def getTxtHdrList(genData, cfgGeneral, cfgTxt):
    pattern = re.compile(r"(IMG_\w+)")
    txtFiles = []

    print("############")
    print("# TXT-Mode #")
    print("############")

    for file in os.listdir(genData.searchDirPath):
        if (file.endswith(cfgTxt.fileEnding.lower()) or file.endswith(cfgTxt.fileEnding.upper())) and cfgTxt.fileNameFilter in file:
            txtFiles.append(file)

    if len(txtFiles) == 0:
        print("No HDR-TXTs found in this directory!")
        return
    else:
        print("\r\nHDR-TXTs Found: %d" % (len(txtFiles)))

    for txtFile in txtFiles:  # Go through every txt-file
        # Create new hdr image array
        genData.hdrList = []
        file = open(os.path.join(genData.searchDirPath, txtFile))

        genData.hdrCount += 1
        print("\r\n| # HDR_%03d" % (genData.hdrCount + genData.hdrCountOffset))
        printSmallTable()

        # go thorugh every line in txt-file
        for _, line in enumerate(file):
            # extract every image name from txt-file
            for match in re.finditer(pattern, line):
                img = match.group(0) + cfgGeneral.imageSrcFileEnding
                if os.path.exists((os.path.join(genData.searchDirPath, img))):
                    printSmallTags(img)
                    genData.hdrList.append(img)
                else:
                    print("'" + img + "' not found! -> skipped")

            genData.hdrList.append(txtFile)
            # append hdr image array to copy list
            genData.hdrMoveList.append(genData.hdrList)

        file.close()
        printSmallTable()


def getExifHdrList(genData, cfgGeneral, cfgExif):
    print("#############")
    print("# EXIF-Mode #")
    print("#############")
    print("")
    print("## Settings:")
    print("# Primary EXIF-Tag:            " + cfgExif.primaryTag_name + " -> Value: " + cfgExif.primaryTag_value)
    print("# Secondary EXIF-Tag:          " + cfgExif.secondaryTag_name + " -> Value: " + cfgExif.secondaryTag_value)
    print("# Tertiary EXIF-Tag:           " + cfgExif.tertiaryTag_name + " -> Value: " + cfgExif.tertiaryTag_value)
    print("# Search Images:               *" + cfgGeneral.imageSrcFileEnding)
    print("# Min Images for HDR-Sequence: " + str(cfgGeneral.hdrSequenceMinNum))
    print("")

    # Find all images in folder and add to file list
    for file in os.listdir(genData.searchDirPath):
        if (file.endswith(cfgGeneral.imageSrcFileEnding)):
            genData.imgFiles.append(file)

    genData.imgFiles.sort()
    genData.hdrCount = 0

    # Find HDR-Sequences
    for img in genData.imgFiles:
        try:
            # read exif info from image without detail search for faster processing.
            # Dont process makernote tags, dont extract the thumbnail image (if any)
            tags = readExif(os.path.join(genData.searchDirPath, img), False, cfgExif.primaryTag_name)
            # if value of exif_primary_tag from image has the specified value, it is part of a HDR-Sequence
            if (str(tags[cfgExif.primaryTag_name]) == cfgExif.primaryTag_value):
                # again read exif info from image, but this time with details
                # -> makernote tags are required to find out with which image a HDR-Sequence starts and stops
                subtags = readExif(os.path.join(genData.searchDirPath, img), True)
                # if value of exif_secondary_tag and exif_tertiary_tag matches, a new HDR-Sequence will be recognized
                if (str(subtags[cfgExif.secondaryTag_name]) == cfgExif.secondaryTag_value) and ((str(subtags[cfgExif.tertiaryTag_name]) == cfgExif.tertiaryTag_value)):
                    # Create new hdr image array
                    genData.hdrList = []
                    genData.hdrList.append(img)
                    # append hdr image array to copy list
                    genData.hdrMoveList.append(genData.hdrList)

                    if genData.hdrCount != 0:
                        printTable()

                    # increase hdr counter and print message
                    genData.hdrCount += 1
                    print("\r\n| # HDR_%03d" % (genData.hdrCount + genData.hdrCountOffset))
                    printTable()
                    printTags("IMG-Name", cfgExif.primaryTag_name, cfgExif.secondaryTag_name, cfgExif.tertiaryTag_name)
                    printTable()

                # if exif_secondary_tag- and exif_tertiary_tag-value does not match image must be part of the previous sequence
                else:
                    genData.hdrList.append(img)

                printTags(img, tags[cfgExif.primaryTag_name],
                          subtags[cfgExif.secondaryTag_name], subtags[cfgExif.tertiaryTag_name])
        except KeyError:
            print("ERROR: Reading EXIF-Data from Image '" + img + "' FAILED! -> image skipped")
        except:
            print("ERROR: Something went wrong during processing Image '" + img + "'!")
    printTable()


def copyHdrList(genData, cfgGeneral):
    imgMoveCount = 0
    moveHdrCount = 0
    skipImgCount = 0

    if not os.path.exists(genData.targetMainDirPath):
        os.makedirs(genData.targetMainDirPath)

    # As long as hdr_move_list is not empty
    while True:
        try:
            # extract first HDR-Sequence form hdr_move_list
            imgMoveList = genData.hdrMoveList.popleft()

            # if extracted HDR-Sequence is equal or larger hdr_sequence_num_min
            # -> it is a complete HDR-Sequence
            if len(imgMoveList) >= cfgGeneral.hdrSequenceMinNum:
                pathExists = True
                # Create sub-directory in hdr-directory if it does nor already exists
                # if directory already exists, try next higher number for directory
                while (pathExists):
                    moveHdrCount += 1
                    dirname = "%s%03d" % (genData.targetSubDirNameMask, moveHdrCount + genData.hdrCountOffset)
                    dirpath = os.path.join(genData.targetMainDirPath, dirname)
                    pathExists = os.path.exists(dirpath)

                for img in imgMoveList:
                    # Create target and source paths for image in imgMoveList
                    sourcePath = os.path.join(genData.searchDirPath, img)
                    targetPath = os.path.join(dirpath, img)
                    # Create copy path for the first image from the HDR-Sequence
                    # -> the script copies the first image from the HDR-Sequence to the HDR-Main-Folder and appends the folder name to the file name
                    # -> makes it easier to look through the HDR-Sequences and to identify which folder has the remaining images
                    targetPathCopy = "%s_HDR_%03d" % (os.path.join(genData.targetMainDirPath, img.replace(
                        cfgGeneral.imageSrcFileEnding, "")), moveHdrCount + genData.hdrCountOffset)

                    # if target directory does not exists create it and copy the first image from the HDR-Sequence
                    if not os.path.exists(dirpath):
                        print("Makedir: %s" % (dirname))
                        os.makedirs(dirpath)
                        if cfgGeneral.previewFiles_create:
                            shutil.copy2(sourcePath, targetPathCopy + cfgGeneral.imageSrcFileEnding)
                            '''
                            if cfgGeneral.previewFiles_convertRawToJpg:
                                # TODO: extracted thumbnail has a really baaaad quality -> do it with https://pypi.org/project/rawpy/
                                tags = readExif(sourcePath, True)
                                thumb = tags['JPEGThumbnail']
                                im = Image.open(io.BytesIO(thumb))
                                im.save(targetPathCopy + ".jpg", "JPEG")

                            else:
                                shutil.copy2(sourcePath, targetPathCopy + cfgGeneral.imageSrcFileEnding)
                            '''

                    # Move the HDR-Sequence to the folder and inform the user about it
                    print("Move: " + img)
                    shutil.move(sourcePath, targetPath)  # move image to target directory
                    imgMoveCount += 1
            else:
                # inform the user which files were skipped
                genData.hdrSkipList.append(imgMoveList)
                for img in imgMoveList:
                    skipImgCount += 1
                    print("HDR-Sequence is less then " + str(cfgGeneral.hdrSequenceMinNum))
                    print("Skip: " + img)

            print(" ")
        except IndexError:
            break

    print("- Finish HDR Move Script -")
    print(" ")
    print("Summary: ")
    print(" Found HDRs: %d" % (genData.hdrCount))
    print(" Moved HDRs: %d" % (moveHdrCount))
    print(" Moved Images:  %d" % (imgMoveCount))
    print(" Skipped HDRs:  %d" % (len(genData.hdrSkipList)))
    print(" Skipped Images:  %d" % (skipImgCount))
    print(" ")

    # TODO: Log-File output


if __name__ == "__main__":  # pragma: no cover
    main()
    sys.exit(0)
