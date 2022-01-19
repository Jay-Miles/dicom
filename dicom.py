#!usr/bin/env python

"""
Name: Medical Physics DICOM project
Date: 19 Jan 2022
Author: Jay Miles
Purpose: SBI102 ICT in the Clinical Environment competencies 3 & 4

UPMC Breast Tomography and FFDM Collection:

https://www.dclunie.com/pixelmedimagearchive/upmcdigitalmammotomocollection/
index.html

-Using Case 6 as an example
-Downloaded file is in .tar.bz2 format and is 172,557 KB
-contains 26 objects - 15 are directories, 11 are (dcm) files
-total size is 1241286528 bytes
-dcm files contain the element '(7fe0, 0010) Pixel Data', which is an array

Largest file is 640869820 bytes:
Case6 [Case6]/20081001 022733 [ - BREAST IMAGING TOMOSYNTHESIS]/Series 73200000 [MG - R CC Breast Tomosynthesis Image]/1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.647.0.dcm

Smallest file is 3262956 bytes:
Case6 [Case6]/20081001 022733 [ - BREAST IMAGING TOMOSYNTHESIS]/Series 72100000 [MG - R CC Tomosynthesis Projection]/1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.637.0.dcm

File structure is:
Case6 [Case6]
    20081001 022733 [ - BREAST IMAGING TOMOSYNTHESIS]
        Series 72100000 [MG - R CC Tomosynthesis Projection]
            1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.637.0.dcm
        Series 72100000 [MG - R MLO Tomosynthesis Projection]
            1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.640.0.dcm
        Series 73100000 [MG - R CC Tomosynthesis Reconstruction]
            1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.643.0.dcm
        Series 73100000 [MG - R MLO Tomosynthesis Reconstruction]
            1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.645.0.dcm
        Series 73200000 [MG - R CC Breast Tomosynthesis Image]
            1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.647.0.dcm
        Series 73200000 [MG - R MLO Breast Tomosynthesis Image]
            1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.649.0.dcm
    20081001 070915 [ - MAMMOGRAM DIGITAL SCR BILAT]
        Series 001 [MG - R CC]
            1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.625.0.dcm
        Series 002 [MG - L CC]
            1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.629.0.dcm
        Series 003 [MG - L MLO]
            1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.631.0.dcm
        Series 004 [MG - R MLO]
            1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.633.0.dcm
    20081001 030956 [ - MAMMOGRAM DIGITAL DX UNILAT RT]
        Series 71100000 [MG - R ML]
            1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.635.0.dcm

"""


import tarfile
import numpy as np
from pydicom import dcmread
from PIL import Image


def look_at_download():
    """ Use the tarfile package to examine Case 6 file contents """

    tar = tarfile.open('MammoTomoUPMC_Case6.tar.bz2', 'r:bz2')

    object_count = 0
    file_count = 0

    largest_file_size = 0
    largest_file = ''

    smallest_file_size = 650000000
    smallest_file = ''

    total_size = 0

    for tarinfo in tar:
        object_count += 1
        total_size += tarinfo.size

        if tarinfo.isreg():
            print("File {a} is {b} bytes.".format(
                a = tarinfo.name,
                b = tarinfo.size
                ))

            if tarinfo.size > largest_file_size:
                largest_file_size = tarinfo.size
                largest_file = tarinfo.name

            if tarinfo.size < smallest_file_size:
                smallest_file_size = tarinfo.size
                smallest_file = tarinfo.name

            file_count += 1

        elif tarinfo.isdir():
            print("Directory {a}".format(a=tarinfo.name))

        else:
            print("{a} is not a file or directory.".format())

    tar.close()

    print('{a} total items, {b} are files, {c} total bytes'.format(
        a = object_count,
        b = file_count,
        c = total_size
        ))

    print('Largest file is {a} bytes: {b}'.format(
        a = largest_file_size,
        b = largest_file
        ))

    print('Smallest file is {a} bytes: {b}'.format(
        a = smallest_file_size,
        b = smallest_file
        ))


def get_smallest_file():
    """ Pull out a single DICOM file to look at """

    tar = tarfile.open('MammoTomoUPMC_Case6.tar.bz2', 'r:bz2')
    tar.extract('Case6 [Case6]/20081001 022733 [ - BREAST IMAGING TOMOSYNTHESIS]/Series 72100000 [MG - R CC Tomosynthesis Projection]/1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.637.0.dcm')
    tar.close()


def single_file_example():
    """ Look at a single dcm file """

    # Specify the path to file
    example_file = 'Case6 [Case6]/20081001 022733 [ - BREAST IMAGING TOMOSYNTHESIS]/Series 72100000 [MG - R CC Tomosynthesis Projection]/1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.637.0.dcm'

    # Read in the dataset as binary using pydicom
    with open(example_file, 'rb') as file_reader:
        dataset = dcmread(file_reader)

    print(dataset)

    # Get the file's pixel data as an array from the pixel_array element
    np_array = dataset.pixel_array
    print(np_array)
    print(np_array.shape)

    # Convert the array to a PNG image using pillow (PIL)

    im = Image.fromarray(np.uint8(np_array))
    im.save('dicom_example.png')
    im.show()


def process_all_case_6():
    """ Extract all contents """

    # Extract all contents of the Case 6 download
    tar = tarfile.open('MammoTomoUPMC_Case6.tar.bz2', 'r:bz2')
    tar.extractall(path='/case_6_contents')
    tar.close()

    # Iterate over all objects in /case_6_contents
    # If the object is a .dcm file,
    # Read it in as a dataset, get its pixel array, and convert to png
    # Store in a separate folder


def main():
    # look_at_download()
    # get_smallest_file()
    single_file_example()
    # process_all_case_6()


if __name__ == '__main__':
    main()
