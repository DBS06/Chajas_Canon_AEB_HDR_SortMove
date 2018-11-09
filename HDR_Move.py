#!/usr/bin/python

import os
import string
import re
import shutil
import sys
import time

print "- Start HDR Move Script -"

directory = ""
txtfiles = []
# pattern = re.compile("(\w\w\w\w+)")
pattern = re.compile("(IMG_\w+)")

while (not os.path.exists(directory)):
    directory = raw_input("input path: ")
    # directory = "C:\Users\phst\OneDrive\Bilder\Photos\URBEX"
    if (directory == ""):
        sys.exit("Exit by User!")
    if (not os.path.exists(directory)):
        print "invalid path!"
    
for file in os.listdir(directory):
    if (file.endswith(".txt") or file.endswith(".TXT")) and "HDR_" in file:
        #print(os.path.join(directory, file))
        txtfiles.append(file)

print " "

if len(txtfiles) == 0:
    sys.exit("No HDR-TXTs found in this directory!")

print "\r\nHDR-TXTs Found: %d" % (len(txtfiles))
proceed = raw_input("Do you want to proceed? (Y)es (N)o: ")
if (proceed is not "Y"):
    sys.exit("Exit by User!")

missing_files = []
count = 0
copy_count = 0
txt_move_count = 0
target_path = ""
main_dir_name = os.path.basename(directory)
target_main_dir_name = main_dir_name + "_HDRs"
target_main_dir_path = os.path.join(directory, target_main_dir_name)

if not os.path.exists(target_main_dir_path):
    os.makedirs(target_main_dir_path)

for txtfile in txtfiles: # Go through every txt-file
    img_count_regex = 0
    img_copy_count = 0
    file = open(os.path.join(directory, txtfile))
    for it, line in enumerate(file): # go thorugh every line in txt-file
        path_exists = True
        while (path_exists): # if directory already exists, try next higher number for directory
            count += 1
            dirname = "%s_HDR_%03d" % (main_dir_name, count)
            dirpath = os.path.join(target_main_dir_path, dirname)
            path_exists = os.path.exists(dirpath)
            
        for match in re.finditer(pattern, line): # extract every image name from txt-file
            img_count_regex += 1
            target_path = os.path.join(dirpath, match.group(0)) + ".CR2"
            source_path = os.path.join(directory, match.group(0)) + ".CR2"
            source_path_copy = "%s_HDR_%03d%s" % (os.path.join(target_main_dir_path, match.group(0)), count, ".CR2")

            if os.path.exists(source_path): # if extracted image name exists
                if not os.path.exists(dirpath): # if target directory does not exists create it
                    print " "
                    print "Makedir: %s" % (dirname)
                    os.makedirs(dirpath)
                    shutil.copy2(source_path, source_path_copy)

                print "File: %d | line %s: %s" % (count, it+1, match.group(0))
                shutil.move(source_path, target_path) # move image to target directory
                # shutil.move(os.path.join(directory, txtfile), target_path)
                copy_count += 1
                img_copy_count += 1
            else: # if image does not exists add it to missing list
                missing_files.append(source_path)
    file.close()
    if (img_copy_count == img_count_regex and img_count_regex > 0): # if all images from on txt-file got copied, remove txt-file
        shutil.move(os.path.join(directory, txtfile), dirpath)
        txt_move_count += 1

print "- Finish HDR Move Script -"
print " "
print "Summary: "
print " Found HDR-TXT-Files: %d"  % (len(txtfiles))
print " Moved HDR-TXT-Files: %d"  % (txt_move_count)
print " Moved Images:  %d" % (copy_count)
print " Missing Images: %d" % (len(missing_files))
print " "

logf = open("log_"+ time.strftime("%Y%m%d_%H%M%S") + ".txt","a+")
logf.write("Summary " + time.strftime("%Y/%m/%d %H:%M:%S") + ":\n")
logf.write(" Found HDR-TXT-Files: " + str(len(txtfiles)) + "\n")
logf.write(" Moved HDR-TXT-Files: " + str(txt_move_count) + "\n")
logf.write(" Moved Images: " + str(copy_count) + "\n")
logf.write(" Missing Images: " + str((len(missing_files))) + "\n")

logf.write("\nMissing Files List:\n")
for miss in missing_files:
    logf.write(miss + "\n")
    print miss
logf.close()

os.system("pause")