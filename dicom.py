#!usr/bin/env python

"""
Name: Medical Physics DICOM project
Date: 19 Jan 2022
Author: Jay Miles
STP: SBI102 ICT in the Clinical Environment competencies 3 & 4

UPMC Breast Tomography and FFDM Collection:

https://www.dclunie.com/pixelmedimagearchive/upmcdigitalmammotomocollection/index.html

-Using Case 6 as an example
-Downloaded file is in .tar.bz2 format and is 172,557 KB
-contains 26 objects - 15 are directories, 11 are (dcm) files
-total file size is 1241286528 bytes
-dcm files contain the element '(7fe0, 0010) Pixel Data', which is an array

Largest file is 640869820 bytes:
1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.647.0.dcm

Smallest file is 3262956 bytes:
1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.637.0.dcm


CURRENT TASKS
-Track time spent on this project: so far 2-3 days
-We need compressed data to experiment with - try compressing and then
decompressing some of the data we already have
-Install DCMTK on work laptop - might need to use CMake, but there also
should be an existing ubuntu package to just install...


"""


import os
import tarfile
import numpy as np

from PIL import Image
from pydicom import dcmread


def look_at_download(parent_dir, archive):
    """ Use the tarfile package to examine contents of a .tar.bz2 archive """

    os.chdir(parent_dir)

    # Open archive
    tar = tarfile.open(archive, 'r:bz2')

    # Define counter variables
    object_count = 0
    file_count = 0
    total_size = 0

    largest_file_size = 0
    largest_file = ''

    smallest_file_size = 650000000  # has to be > smallest file size
    smallest_file = ''

    # Iterate over all objects
    for tarinfo in tar:

        object_count += 1
        total_size += tarinfo.size

        # Print name and size of any regular files
        if tarinfo.isreg():
            file_count += 1

            print("File {} is {} bytes.".format(tarinfo.name, tarinfo.size))

            if tarinfo.size > largest_file_size:
                largest_file_size = tarinfo.size
                largest_file = tarinfo.name

            if tarinfo.size < smallest_file_size:
                smallest_file_size = tarinfo.size
                smallest_file = tarinfo.name

        # Print the name of any directories
        elif tarinfo.isdir():
            print("Directory {}".format(tarinfo.name))

        else:
            print("{} is not a file or directory.".format(tarinfo.name))

    # Close the archive
    tar.close()

    # Print info
    print('{} total items, {} are files, {} total bytes'.format(
        object_count,
        file_count,
        total_size
        ))

    print('Largest file is {} bytes: {}'.format(
        largest_file_size,
        largest_file
        ))

    print('Smallest file is {} bytes: {}'.format(
        smallest_file_size,
        smallest_file
        ))


def identify_largest_file(parent_dir, archive):
    """
    Use the tarfile package to find the largest file in a .tar.bz2 archive
    """

    os.chdir(parent_dir)

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


def identify_smallest_file(extracted_path):
    """
    Use the tarfile package to find the smallest file in a .tar.bz2 archive.
    """

    # Counter must start higher than largest file size
    smallest_file_size = 650000000
    smallest_file = ''

    # Iterate over extracted archive, look only at files
    for root, dirs, files in os.walk(extracted_path):
        for file in files:

            # Look at .dcm files, get their filepath and size
            if file.lower().endswith('.dcm'):
                filepath = os.path.join(root, file)
                file_size = os.path.getsize(filepath)

                # If they're smaller than the counter, update it
                if file_size < smallest_file_size:
                    smallest_file = filepath
                    smallest_file_size = file_size

    return smallest_file


def extract_all_files(parent_dir, archive):
    """ Extract all contents of a .tar.bz2 archive into a new directory. """

    os.chdir(parent_dir)

    tar = tarfile.open(archive, 'r:bz2')
    tar.extractall()
    tar.close()


def smallest_file_example(extracted_path):
    """
    Find the smallest file in a (already extracted) .tar.bz2 archive,
    convert it to an image array, and save it as a PNG
    """

    filepath = identify_smallest_file(extracted_path)
    filename = filepath.split('\\')[-1]
    file_size = os.path.getsize(filepath)
    print('smallest file ({} bytes): {}'.format(file_size, filename))
    print('full path: {}'.format(filepath))

    # Read in the dataset as binary using pydicom
    with open(filepath, 'rb') as file_reader:
        dataset = dcmread(file_reader)

    # Get Pixel Data as numpy array using pydicom pixel_array syntax
    image_array = dataset.pixel_array

    if len(image_array.shape) == 2:  # if the file is not multiframe
        im = Image.fromarray(np.uint8(image_array))
        im.show()

    elif len(image_array.shape) == 3:   # if the file IS multiframe
        im = Image.fromarray(np.uint8(image_array[0]))
        im.show()


def make_images_folder(parent_dir):
    """ Make a new directory to hold images """

    new_dir = 'Images'
    path = os.path.join(parent_dir, new_dir)

    try:
        os.mkdir(path)

    except FileExistsError:
        pass


def process_whole_directory(parent_dir, extracted_archive):
    """
    Iterate over the contents of a directory, convert each .dcm file to a
    numpy array, and save as PNG image
    """

    os.chdir(parent_dir)
    make_images_folder(parent_dir)
    images_path = os.path.join(parent_dir, 'Images')

    # Iterate over the extracted archive contents
    for root, dirs, files in os.walk(extracted_archive):

        # Look only at files
        for file in files:

            # Look only at .dcm files
            if file.lower().endswith('.dcm'):

                # Read in the dataset as binary using pydicom
                filepath = os.path.join(root, file)
                filename = file[:-4]

                with open(filepath, 'rb') as file_reader:
                    dataset = dcmread(file_reader)

                # Get Pixel Data as array from pixel_array element
                image_array = dataset.pixel_array

                # Deal with single-frame files
                if len(image_array.shape) == 2:

                    # Create an image
                    im = Image.fromarray(np.uint8(image_array))

                    # Save as .png in the Images directory
                    os.chdir(images_path)
                    im.save('{}.png'.format(filename))
                    os.chdir(parent_dir)

                # Deal with multiframe files
                if len(image_array.shape) == 3:

                    # Create a new subdirectory to hold the images
                    file_dir = '{}'.format(filename)
                    file_dir_path = os.path.join(images_path, file_dir)

                    try:
                        os.mkdir(file_dir_path)

                    except FileExistsError:
                        continue

                    # Go into that subdirectory and create/save all the images
                    os.chdir(file_dir_path)

                    i = 1
                    for frame in image_array:
                        im = Image.fromarray(np.uint8(frame))
                        im.save('{}_{}.png'.format(filename, i))
                        i += 1

                    # Go back into the main project directory
                    os.chdir(parent_dir)


def compression_test(extracted_archive):
    """ Compress the extracted directory and re-archive as .tar.bz2, then
    extract again and decompress to check no loss of data """

    # I need CharPyLS for this but it is not co-operating


def main():
    parent_dir = 'C:\\Users\\Jay\\Projects\\dicom\\dicom'  # Archive location

    archive = 'MammoTomoUPMC_Case6.tar.bz2'  # Downloaded archive file

    extracted_archive = 'Case6 [Case6]'  # Name of extracted archive folder
    extracted_path = os.path.join(parent_dir, extracted_archive)

    # look_at_download(parent_dir, archive)
    # extract_smallest_file(parent_dir, archive)
    # extract_all_files(parent_dir, archive)
    # smallest_file_example(extracted_path)
    # process_whole_directory(parent_dir, extracted_archive)


if __name__ == '__main__':
    main()
