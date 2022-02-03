# dicom
Project to extract human-readable metadata and image from DFF files

The UPMC Breast Tomography and FFDM Collection has a series of .tar.bz2
archives containing uncompressed DICOM Format Files. It can be accessed
at:

https://www.dclunie.com/pixelmedimagearchive/upmcdigitalmammotomocollection/index.html

This project is using Case 6 as an example. The downloaded file is named
'MammoTomoUPMC_Case6.tar.bz2' and is 172,557 KB in size. It contains 26 
objects: 15 directories and 11 .dcm files, with a total file size of 
1241286528 bytes. The largest file
(1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.647.0.dcm) is 
640869820 bytes; the smallest 
(1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.637.0.dcm) is 
3262956 bytes.

These .dcm files contain the element '(7fe0, 0010) Pixel Data', which is
 an array of numbers representing an image. pydicom is able to directly 
 access a PixelData element value as a numpy array through the syntax 
 <dataset>.pixel_array.

General overview:\
-Download a case archive in .tar.bz2 format\
-Extract archive contents with the tarfile module\
-Iterate over the extracted contents and look at DICOM files\
-For each file, open it and dump the metadata\
-Extract pixel data into a numpy array using pydicom\
-Convert the array to an image and save as .png using pillow (PIL)\
-Account for multiframe files, which contain multiple images\
