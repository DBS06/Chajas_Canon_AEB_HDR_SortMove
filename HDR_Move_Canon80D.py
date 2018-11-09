#!/usr/bin/python

from collections import deque
import exifread
import os
import string
import re
import shutil
import sys
import time

# Class to define the EXIF-Tags which indicates that a picture is part of a HDR-Sequence
class ExifTag:
    def __init__(self, name, val):
        self.name = name # IFD name followed by the tag name. For example: 'EXIF DateTimeOriginal', 'Image Orientation', 'MakerNote FocusMode'
        self.val = val # value of the tag

#############################
### Script Settings
#############################

### Common Stuff
image_file_ending = ".CR2"

### Printing Stuff

# placeholders for printing
print_img_plh = 13
print_tag_plh = 23
# default stop tag
DEFAULT_STOP_TAG = ""

### HDR-Sequence Stuff

# minimum number of images which a HDR-Sequence must have
hdr_sequence_num_min = 3

## EXIF-Tags which indicates that a picture is part of a HDR-Sequence:
# primary-tag is used to find the images which are part of an HDR-Sequence
# this tag should be part of 'Standard'-EXIF-Tags to increase the search speed, otherwise it would be really slow
exif_primary_tag = ExifTag("EXIF ExposureMode", "Auto Bracket")
# secondary- and tertiary-tag are used to find the beginning of a HDR-Sequence
exif_secondary_tag = ExifTag("MakerNote BracketMode", "AEB")
exif_tertiary_tag = ExifTag("MakerNote BracketValue", "0")

#############################
#############################


#############################
### Functions
#############################

def read_exif(path, exif_details, stop_tag=DEFAULT_STOP_TAG):
    img = open(path, 'rb')
    tags_img = exifread.process_file(img,  details=exif_details, stop_tag=stop_tag)
    img.close()
    return tags_img

def print_table():
    print "+-%s+-%s+-%s+-%s+" % ("-" * print_img_plh, "-" * print_tag_plh, "-" * print_tag_plh, "-" * print_tag_plh)
    return

def print_tags(img, tag1, tag2, tag3):
    print "| %-*s| %-*s| %-*s| %-*s|" % (print_img_plh, img, print_tag_plh, tag1, print_tag_plh, tag2, print_tag_plh, tag3)
    return

#############################
#############################


#############################
### MAIN
#############################

print "###################################"
print "# Start HDR Move Canon 80D Script #"
print "###################################"
print ""

print "## Settings:"
print "# Primary EXIF-Tag:            " + exif_primary_tag.name + " -> Value: " + str(exif_primary_tag.val)
print "# Secondary EXIF-Tag:          " + exif_secondary_tag.name + " -> Value: " + str(exif_secondary_tag.val)
print "# Tertiary EXIF-Tag:           " + exif_tertiary_tag.name + " -> Value: " + str(exif_tertiary_tag.val)
print "# Search Images:               *" + image_file_ending
print "# Min Images for HDR-Sequence: " + str(hdr_sequence_num_min)
print ""

# Global Variables
directory = ""
imgFiles = []
hdr_move_list = deque()
hdr_skip_list = deque()
hdr_count = 0
hdr_list = []

# Get path to image folder and proof if it exists
while (not os.path.exists(directory)):
    directory = raw_input("Path to Image Folder (abort with hit 'RETURN'): ")
    # directory = "C:\Users\phst\Pictures\Test_Pictures"
    if (directory == ""):
        sys.exit("Exit by User!")
    if (not os.path.exists(directory)):
        print "invalid path!"

# Find all images in folder and add to file list
for file in os.listdir(directory):
    if (file.endswith(image_file_ending)):
        #print(os.path.join(directory, file))
        imgFiles.append(file)

print " "
target_path = ""
main_dir_name = os.path.basename(directory)
target_main_dir_name = main_dir_name + "_HDRs"
target_main_dir_path = os.path.join(directory, target_main_dir_name)

# Find HDR-Sequences
for img in imgFiles:
    # read exif info from image without detail search for faster processing.
    # Dont process makernote tags, dont extract the thumbnail image (if any)
    tags = read_exif(os.path.join(directory, img), False, exif_primary_tag.name)
    # if value of exif_primary_tag from image has the specified value, it is part of a HDR-Sequence
    if (str(tags[exif_primary_tag.name]) == exif_primary_tag.val):
        # again read exif info from image, but this time with details
        # -> makernote tags are required to find out with which image a HDR-Sequence starts and stops
        subtags = read_exif(os.path.join(directory, img), True)
        # if value of exif_secondary_tag and exif_tertiary_tag matches, a new HDR-Sequence will be recognized
        if (str(subtags[exif_secondary_tag.name]) == exif_secondary_tag.val) and ((str(subtags[exif_tertiary_tag.name]) == exif_tertiary_tag.val)):
            # Create new hdr image array
            hdr_list = []
            hdr_list.append(img)
            # append hdr image array to copy list
            hdr_move_list.append(hdr_list)

            if hdr_count != 0:
                print_table()

            # increase hdr counter and print message
            hdr_count += 1
            print "\r\n| # HDR_%03d" % (hdr_count)
            print_table()
            print_tags("IMG-Name", exif_primary_tag.name, exif_secondary_tag.name, exif_tertiary_tag.name)
            print_table()

        # if exif_secondary_tag- and exif_tertiary_tag-value does not match image must be part of the previous sequence
        else:
            hdr_list.append(img)
        print_tags(img, tags[exif_primary_tag.name], subtags[exif_secondary_tag.name], subtags[exif_tertiary_tag.name])
print_table()

# Inform user about the search result

hdrs_found = len(hdr_move_list)
if hdrs_found == 0:
    sys.exit("No HDRs found in this directory!")

print "\r\nHDRs Found: %d" % (hdrs_found)

# Ask user if he wants to 
proceed = raw_input("Do you want to start the moving the found HDR-Sequences? (Y)es (N)o: ")
if (proceed is not "Y"):
    sys.exit("Exit by User!")

img_move_count = 0
move_hdr_count = 0
skip_img_count = 0

if not os.path.exists(target_main_dir_path):
    os.makedirs(target_main_dir_path)

# As long as hdr_move_list is not empty
while True:
    try:
        # extract first HDR-Sequence form hdr_move_list
        img_move_list = hdr_move_list.popleft()

        # if extracted HDR-Sequence is equal or larger hdr_sequence_num_min
        # -> it is a complete HDR-Sequence
        if len(img_move_list) >= hdr_sequence_num_min:
            path_exists = True
            # Create sub-directory in hdr-directory if it does nor already exists
            # if directory already exists, try next higher number for directory
            while (path_exists):
                move_hdr_count += 1
                dirname = "%s_HDR_%03d" % (main_dir_name, move_hdr_count)
                dirpath = os.path.join(target_main_dir_path, dirname)
                path_exists = os.path.exists(dirpath)
            
            for img in img_move_list:
                # Create target and source paths for image in img_move_list
                source_path = os.path.join(directory, img)
                target_path = os.path.join(dirpath, img)
                # Create copy path for the first image from the HDR-Sequence
                # -> the script copies the first image from the HDR-Sequence to the HDR-Main-Folder and appends the folder name to the file name
                # -> makes it easier to look through the HDR-Sequences and to identify which folder has the remaining images
                target_path_copy = "%s_HDR_%03d%s" % (os.path.join(target_main_dir_path, img.replace(image_file_ending, "") ), move_hdr_count, image_file_ending)

                # if target directory does not exists create it and copy the first image from the HDR-Sequence
                if not os.path.exists(dirpath): 
                    print "Makedir: %s" % (dirname)
                    os.makedirs(dirpath)
                    shutil.copy2(source_path, target_path_copy)

                # Move the HDR-Sequence to the folder and inform the user about it
                print "Move: " + img
                shutil.move(source_path, target_path) # move image to target directory
                img_move_count += 1
        else:
            
            # inform the user which files were skipped
            hdr_skip_list.append(img_move_list)
            for img in img_move_list:
                skip_img_count += 1
                print "HDR-Sequence is less then " + str(hdr_sequence_num_min)
                print "Skip: " + img

        print " "
    except IndexError:
        break

print "- Finish HDR Move Script -"
print " "
print "Summary: "
print " Found HDRs: %d"  % (hdrs_found)
print " Moved HDRs: %d"  % (move_hdr_count)
print " Moved Images:  %d" % (img_move_count)
print " Skipped HDRs:  %d" % (len(hdr_skip_list))
print " Skipped Images:  %d" % (skip_img_count)
print " "

logf = open("log_80D_"+ time.strftime("%Y%m%d_%H%M%S") + ".txt","a+")
logf.write("Summary " + time.strftime("%Y/%m/%d %H:%M:%S") + ":\n")
logf.write(" Found HDRs: " + str(hdrs_found) + "\n")
logf.write(" Moved HDRs: " + str(move_hdr_count) + "\n")
logf.write(" Moved Images: " + str(img_move_count) + "\n")
logf.write(" Skipped HDRs: " + str(len(hdr_skip_list)) + "\n")
logf.write(" Skipped Images: " + str(skip_img_count) + "\n")

logf.write("\nSkipped Files List:\n")

log_skip_sequ_counter = 0
while True:
    try:
        img_skip_list = hdr_skip_list.popleft()
        log_skip_sequ_counter += 1

        tmp_str = "Skipped HDR-Sequence: " + str(log_skip_sequ_counter)
        print tmp_str
        logf.write(tmp_str + "\n")

        for img in img_skip_list:
            tmp_str = str(img)
            print tmp_str
            logf.write(tmp_str + "\n")
        logf.write("\n")
    except IndexError:
        break
logf.close()

os.system("pause")

#############################
#############################

# while True:
#     try:
#         hdr_copy_list = cr2_copy_list.popleft()
#         print "\r\nHDR_%03d" % (move_hdr_count)
#         move_hdr_count += 1
#         for img in hdr_copy_list:
#             print img
#         print " "
#     except IndexError:
#         break