# Chaja's - Canon AEB HDR SortMove

Is a python script which helps to sort HDR images.

Originally this Script was written to work with Magic-Lantern, but Magic-Lantern isn’t available for Canon 60D+ Models, therefore I wrote a second script which reads and analyzes the EXIF-Data and detects the HDR sequences.
This repository includes two scripts:

* **HDR_Move_EXIF.py:** This is the general purpose script for Canon EOS Cameras to sort HDR-Sequences which were shot with *Auto Exposure Bracketing (AEB)*.
* **HDR_Move_ML.py:** Is for images which are taken with Magic-Lanterns “Advanced Bracket” mode. **Note:** The option to create a txt-file inside the “Post scripts” setting must be enabled. The created *.txt* file contains the HDR-Sequence.

## Supported and tested Models

**HDR_Move_EXIF.py** tested with Canon EOS 60D and 80D. Will be constantly supported and updated if necessary or requested.

**HDR_Move_EXIF.py** tested with Canon EOS 60D and Magic-Lantern-Nightly.2018Jul03.60D111. Will not be constantly supported and updated, because I am not using Magic-Lantern anymore (not available for my 80D). But anyways, I don't think there will be a change needed.

## Dependencies

see *requirements.txt*

install with:
`pip install -r requirements.txt`

## Usage HDR_Move_EXIF.py

### Start the Script:

Start the script with `python HDR_Move_EXIF.py` and you will see:

```
###########################################
# Chaja's - Canon AEB HDR SortMove - EXIF #
###########################################

## Settings:
# Primary EXIF-Tag:            EXIF ExposureMode -> Value: Auto Bracket
# Secondary EXIF-Tag:          MakerNote BracketMode -> Value: AEB
# Tertiary EXIF-Tag:           MakerNote BracketValue -> Value: 0
# Search Images:               *.CR2
# Min Images for HDR-Sequence: 3

Path to Image Folder (abort with hit 'RETURN'):
```

Enter the path and the search will be started.  
*Note:* The name of the parent folder will be the name for the subfolders.  
For example if the path would be `C:\This\is\my\path\Linked Living` the following subfolders in `Linked Living` will be created:  

* Linked Living_HDRs
  * Linked Living_HDR_001
  * ...
  * Linked Living_HDR_006

Inside of the parent HDR folder (`Linked Living_HDRs`) the first image of every HDR-Sequence will be stored and renamed i.e. from `IMG_9053.CR2` to `IMG_9053_HDR_001.CR2`.  
This helps to get an overview which HDRs you have made and it will also acts as a preview-image.

Inside of the subfolder `Linked Living_HDR_001` the complete HDR-Sequence will be stored, for this example folder this would be:  

* Linked Living_HDR_001
  * IMG_9053.CR2
  * IMG_9054.CR2
  * IMG_9055.CR2

**Note:** The number inside of the folder name `Linked Living_HDR_001` -> `001` corresponds with the number of the preview-image -> `IMG_9053_HDR_001.CR2` -> `001`.  

### Searching for HDR-Sequences

After entering the path to the image folder the script searches for HDR-Sequences. You will see the following output:

```
| # HDR_001
+--------------+------------------------+------------------------+------------------------+
| IMG-Name     | EXIF ExposureMode      | MakerNote BracketMode  | MakerNote BracketValue |
+--------------+------------------------+------------------------+------------------------+
| IMG_9053.CR2 | Auto Bracket           | AEB                    | 0                      |
| IMG_9054.CR2 | Auto Bracket           | AEB                    | 65504                  |
| IMG_9055.CR2 | Auto Bracket           | AEB                    | 32                     |
+--------------+------------------------+------------------------+------------------------+

[...]

| # HDR_006
+--------------+------------------------+------------------------+------------------------+
| IMG-Name     | EXIF ExposureMode      | MakerNote BracketMode  | MakerNote BracketValue |
+--------------+------------------------+------------------------+------------------------+
| IMG_9096.CR2 | Auto Bracket           | AEB                    | 0                      |
| IMG_9097.CR2 | Auto Bracket           | AEB                    | 65472                  |
| IMG_9098.CR2 | Auto Bracket           | AEB                    | 64                     |
+--------------+------------------------+------------------------+------------------------+

HDRs Found: 6
Do you want to start the moving the found HDR-Sequences? (Y)es (N)o: 
```

If you like you can prove the search result, if you are satisfied press `Y` if you want to start the moving process, or anything else to abort.

### Moving HDR-Sequences

After starting the moving process you will see the following output:

```
Makedir: Linked Living_HDR_001
Move: IMG_9053.CR2
Move: IMG_9054.CR2
Move: IMG_9055.CR2

[...]

Makedir: Linked Living_HDR_006
Move: IMG_9096.CR2
Move: IMG_9097.CR2
Move: IMG_9098.CR2

- Finish HDR Move Script -

Summary:
 Found HDRs: 6
 Moved HDRs: 6
 Moved Images:  18
 Skipped HDRs:  0
 Skipped Images:  0

Press any key to continue . . .
```

And the searching and moving of HDR-Sequences is complete and the following folder and file structure was generated:

* Linked Living_HDRs
  * Linked Living_HDR_001
    * IMG_9053.CR2
    * IMG_9054.CR2
    * IMG_9055.CR2
  * ...
  * Linked Living_HDR_006
    * IMG_9096.CR2
    * IMG_9097.CR2
    * IMG_9098.CR2
  * IMG_9053_HDR_001.CR2
  * ...
  * IMG_9096_HDR_006.CR2

## Usage HDR_Move_ML.py

Similar to *Usage HDR_Move_EXIF.py*, except that it will rely on the created *.txt* files by Magic-Lantern and not on the EXIF-Data.  
**For example:** The file `HDR_3800.txt` contains the following text:  
`IMG_3800.JPG IMG_3801.JPG IMG_3802.JPG IMG_3803.JPG IMG_3804.JPG`
The script will search for the corresponding images and will sort the images as described in **Usage HDR_Move_EXIF.py**.
