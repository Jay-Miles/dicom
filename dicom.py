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
-total file size is 1241286528 bytes
-dcm files contain the element '(7fe0, 0010) Pixel Data', which is an array

Largest file is 640869820 bytes:
1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.647.0.dcm

Smallest file is 3262956 bytes:
1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.637.0.dcm

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


import os
import tarfile
import numpy as np

from pathlib import Path
from PIL import Image
from pydicom import dcmread


def look_at_download(archive):
    """ Use the tarfile package to examine contents of a .tar.bz2 archive """

    # Open archive
    tar = tarfile.open(archive, 'r:bz2')

    # Define counter variables
    object_count = 0
    file_count = 0
    total_size = 0

    largest_file_size = 0
    largest_file = ''

    smallest_file_size = 650000000
    smallest_file = ''

    # Iterate over all objects
    for tarinfo in tar:

        object_count += 1
        total_size += tarinfo.size

        # Print name and size of any regular files
        if tarinfo.isreg():
            file_count += 1

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

        # Print the name of any directories
        elif tarinfo.isdir():
            print("Directory {a}".format(a=tarinfo.name))

        else:
            print("{a} is not a file or directory.".format())

    # Close the archive
    tar.close()

    # Print info
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


def identify_largest_file(archive):
    """
    Use the tarfile package to find the largest file in a .tar.bz2 archive.
    """

    tar = tarfile.open(archive, 'r:bz2')

    largest_file_size = 0
    largest_file = ''

    for tarinfo in tar:
        if tarinfo.isreg():
            if tarinfo.size < largest_file_size:
                largest_file_size = tarinfo.size
                largest_file = tarinfo.name

    tar.close()

    return largest_file


def identify_smallest_file(archive):
    """
    Use the tarfile package to find the smallest file in a .tar.bz2 archive.
    """

    tar = tarfile.open(archive, 'r:bz2')

    smallest_file_size = 650000000  # must be > biggest file in archive
    smallest_file = ''

    for tarinfo in tar:
        if tarinfo.isreg():
            if tarinfo.size < smallest_file_size:
                smallest_file_size = tarinfo.size
                smallest_file = tarinfo.name

    tar.close()

    return smallest_file


def extract_all_files(archive):
    """ Extract all contents of a .tar.bz2 archive into a new directory. """

    tar = tarfile.open(archive, 'r:bz2')
    tar.extractall()
    tar.close()


def smallest_file_example(archive):
    """
    Extract the smallest file from a .tar.bz2 archive, convert it to an
    image array, and save it as a PNG.
    """

    filepath = identify_smallest_file(archive)
    print('filepath is: {a}'.format(a = filepath))

    split_path = filepath.split('/')
    last_path = split_path[-1]
    filename = last_path[:-4]
    print('filename is: {a}'.format(a = filename))

    # Read in the dataset as binary using pydicom
    with open(filepath, 'rb') as file_reader:
        dataset = dcmread(file_reader)

    # Get the file's Pixel Data as an array via the pixel_array element
    image_array = dataset.pixel_array
    # print(dataset)
    # print(image_array)
    # print(image_array.shape)

    # Create an image using from the array using pillow (PIL)
    im = Image.fromarray(np.uint8(image_array))

    # Save the image in .png format
    im.show()
    im.save('{a}.png'.format(a = filename))


def process_whole_directory():
    """
    Iterate over the contents of a directory, convert each .dcm file to a
    numpy array, and save as PNG image.
    """

    # Iterate over the extracted contents
    for root, dirs, files in os.walk('Case6 [Case6]'):

        # Look only at files
        for file in files:

            # Look only at .dcm files
            if file.lower().endswith('.dcm'):

                # Read in the dataset as binary using pydicom
                filepath = os.path.join(root, file)

                # Read in the dataset as binary using pydicom
                with open(filepath, 'rb') as file_reader:
                    dataset = dcmread(file_reader)

                try:  # try to get Pixel Data as array from pixel_array element
                    image_array = dataset.pixel_array
                    # print(image_array)
                    # print(image_array.shape)

                    try:  # try to create image and save as .png
                        im = Image.fromarray(np.uint8(image_array))
                        im.save('{a}.png'.format(a = file[:-4]))

                    except TypeError:
                        continue

                except MemoryError:
                    continue


def main():
    archive = 'MammoTomoUPMC_Case6.tar.bz2'  # Downloaded Case 6 archive

    # look_at_download(archive)
    # extract_smallest_file(archive)
    # extract_all_files(archive)
    # smallest_file_example(archive)
    process_whole_directory()


if __name__ == '__main__':
    main()
