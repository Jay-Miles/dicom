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


def identify_largest_file(parent_dir, archive):
    """
    Use the tarfile package to find the largest file in a .tar.bz2 archive.
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


def identify_smallest_file(parent_dir, archive):
    """
    Use the tarfile package to find the smallest file in a .tar.bz2 archive.
    """

    os.chdir(parent_dir)

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


def extract_all_files(parent_dir, archive):
    """ Extract all contents of a .tar.bz2 archive into a new directory. """

    os.chdir(parent_dir)

    tar = tarfile.open(archive, 'r:bz2')
    tar.extractall()
    tar.close()


def smallest_file_example(parent_dir, archive):
    """
    Find the smallest file in a (previously extracted) .tar.bz2 archive,
    convert it to an image array, and save it as a PNG.
    """

    filepath = identify_smallest_file(parent_dir, archive)
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

    # Create an image using from the array using pillow (PIL)
    im = Image.fromarray(np.uint8(image_array))

    # Save the image in .png format
    im.show()
    im.save('{a}.png'.format(a = filename))


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
    numpy array, and save as PNG image.
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
                    im.save('{a}.png'.format(a = filename))
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
                        im.save('{0}_{1}.png'.format(filename, i))
                        i += 1

                    # Go back into the main project directory
                    os.chdir(parent_dir)


def main():
    parent_dir = 'C:\\Users\\Jay\\Projects\\dicom\\dicom'  # archive location
    archive = 'MammoTomoUPMC_Case6.tar.bz2'  # Downloaded archive file
    extracted_archive = 'Case6 [Case6]'  # name of extracted archive folder

    # look_at_download(parent_dir, archive)
    # extract_smallest_file(parent_dir, archive)
    # extract_all_files(parent_dir, archive)
    # smallest_file_example(parent_dir, archive)
    process_whole_directory(parent_dir, extracted_archive)


if __name__ == '__main__':
    main()
