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


import jpeg_ls
import numpy as np
import os
import subprocess
import tarfile

from PIL import Image
from pydicom import dcmread, dcmwrite
from pydicom.uid import RLELossless

# from pydicom.encaps import encapsulate, encapsulate_extended
# from typing import List, Tuple


def look_at_download(parent_dir, archive):
    """ Use tarfile to examine contents of a .tar.bz2 archive """

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


def extract_all_files(parent_dir, archive):
    """ Extract contents of .tar.bz2 archive into new directory """

    os.chdir(parent_dir)

    tar = tarfile.open(archive, 'r:bz2')
    tar.extractall()
    tar.close()


def make_new_folder(parent_dir, name):
    """ Make a new directory and return its path """

    new_dir = os.path.join(parent_dir, name)

    try:
        os.mkdir(new_dir)

    except FileExistsError:
        pass

    return new_dir


def process_for_images(images_path, extracted_path):
    """ Iterate over contents of a directory, convert each .dcm file to
    a numpy array, save as PNG image """

    # Iterate over the extracted archive contents
    for root, dirs, files in os.walk(extracted_path):

        # Look only at files
        for file in files:

            # Look only at .dcm files
            if file.lower().endswith('.dcm'):

                # Read in the dataset as binary using pydicom
                filepath = os.path.join(root, file)

                with open(filepath, 'rb') as file_reader:
                    ds = dcmread(file_reader)

                # Get acquisition date and patient name, create file title

                # pt_name = ds['PatientName']  # use this for actual pt files
                pt_name = ds['SOPInstanceUID'][-5:-2]  # use for example files

                image_date = ds['AcquisitionDate'][:]
                image_time = ds['AcquisitionTime'][:-4]

                title = '{}_{}_{}'.format(
                    image_date,
                    image_time,
                    pt_name)

                # Get Pixel Data as array from pixel_array element
                image_array = ds.pixel_array

                # Deal with single-frame files
                if len(image_array.shape) == 2:

                    # Create an image
                    im = Image.fromarray(np.uint8(image_array))

                    # Save as .png in the Images directory
                    im_filename = '{}.png'.format(title)
                    im_path = os.path.join(images_path, im_filename)
                    im.save(im_path)

                # Deal with multiframe files
                elif len(image_array.shape) == 3:

                    # Create a new subdirectory to hold the images
                    file_dir_path = os.path.join(images_path, title)

                    try:
                        os.mkdir(file_dir_path)

                    except FileExistsError:
                        continue

                    i = 1
                    for frame in image_array:
                        im = Image.fromarray(np.uint8(frame))

                        im_filename = '{}_frame_{}.png'.format(title, i)
                        im_path = os.path.join(file_dir_path, im_filename)
                        im.save(im_path)

                        i += 1


def process_for_metadata(metadata_path, extracted_path):
    """ Iterate over the contents of a directory and dump the metadata
    for each .dcm file. N.B. single- and multi-frame files don't need to
    be dealt with differently, as this only affects PixelData (which
    doesn't get output here) """

    # Iterate over the extracted archive contents
    for root, dirs, files in os.walk(extracted_path):

        # Look only at files
        for file in files:

            # Look only at .dcm files
            if file.lower().endswith('.dcm'):

                # Read in the dataset
                filepath = os.path.join(root, file)

                with open(filepath, 'rb') as file_reader:
                    ds = dcmread(file_reader)

                # Get details to construct filename

                # pt_name = ds['PatientName']  # use this for actual pt files
                pt_name = ds['SOPInstanceUID'][-5:-2]  # use for example files

                image_date = ds['AcquisitionDate'][:]
                image_time = ds['AcquisitionTime'][:-4]

                if len(ds.pixel_array.shape) == 2:
                    frames = 'single_frame'
                elif len(ds.pixel_array.shape) == 3:
                    frames = 'multi_frame'

                filename = '{}_{}_{}_{}.txt'.format(
                    image_date,
                    image_time,
                    pt_name,
                    frames,
                    )

                new_filepath = os.path.join(metadata_path, filename)

                # Run dcmdump via command line to get text output
                dcm_call = ['dcmdump', '-M', str(filepath)]

                dcm_dump = subprocess.run(
                    dcm_call,
                    text = True,
                    capture_output = True,
                    )

                dcm_text = dcm_dump.stdout

                # Write this to a text file
                with open(new_filepath, 'w') as file_writer:
                    file_writer.write(dcm_text)


def compress_with_dcmtk(compression_path, example_path):
    """ Compress an example .dcm file, then decompress again to check
    for data loss. Loses 170 bytes of data. Uses RLELossLess
    (de)compression via dcm toolkit (dcmtk), which is run from the
    command line.

    Original file size:     3262956
    Compressed file size:   3063770
    Decompressed file size: 3262786
    """

    # Define the file to use
    original_file_size = os.path.getsize(example_path)
    print('Original file size: {}'.format(original_file_size))

    # Create a compressed RLELossLess file with dcmtk
    compressed_file = os.path.join(
        compression_path,
        'after_compression.dcm'
        )

    compress_command = ['dcmcrle', example_path, compressed_file]
    subprocess.run(compress_command)

    # Look at the compressed file size
    compressed_file_size = os.path.getsize(compressed_file)
    print('Compressed file size: {}'.format(compressed_file_size))

    # Decompress the compressed file with dcmtk
    decompressed_file = os.path.join(
        compression_path,
        'after_decompression.dcm'
        )

    decompress_command = ['dcmdrle', compressed_file, decompressed_file]
    subprocess.run(decompress_command)

    # Look at the decompressed file size
    decompressed_file_size = os.path.getsize(decompressed_file)
    print('Decompressed file size: {}'.format(decompressed_file_size))


def compress_with_charpyls(compression_path, example_path):
    """ (De)compression using JPEGLSLOsslessa via the CharPyLS package.
    Package must be installed directly from GitHub repo, not via pip.

    Compressing and then decompressing the array in-place, without
    writing out to a compressed file and reading in again to decompress,
    results in no loss of data and the original and final arrays are
    identical.
    """

    # Define the file to use and read in data
    original_file_size = os.path.getsize(example_path)
    print('Original file size: {}'.format(original_file_size))

    with open(example_path, 'rb') as reader:
        ds = dcmread(reader)

    original_array = ds.pixel_array

    # Compress the PixelData array
    compressed_array = jpeg_ls.encode(original_array)
    ds.PixelData = compressed_array

    # Write the dataset with compressed array to file
    compressed_file = os.path.join(
        compression_path,
        'after_compression.dcm'
        )

    with open(compressed_file, 'wb') as writer:
        dcmwrite(writer, ds, write_like_original = False)

    # Get the size of the file with compressed array
    compressed_file_size = os.path.getsize(compressed_file)
    print('Compressed file size: {}'.format(compressed_file_size))

    # Decompress existing array (don't read in compressed file)
    decompressed_array = jpeg_ls.decode(compressed_array)
    ds.PixelData = decompressed_array

    # Write dataset with decompressed array to file
    decompressed_file = os.path.join(
        compression_path,
        'after_decompression.dcm'
        )

    with open(decompressed_file, 'wb') as writer:
        dcmwrite(writer, ds, write_like_original = False)

    # Get the size of the file with decompressed array
    decompressed_file_size = os.path.getsize(decompressed_file)
    print('Decompressed file size: {}'.format(decompressed_file_size))

    # Confirm that the original and decompressed array are identical
    if (original_array == decompressed_array).all():
        print('original and decompressed arrays are identical')


    # # Try reading in compressed file and decompressing, then writing out
    # with open(compressed_file, 'rb') as reader:
    #     ds2 = dcmread(reader)

    # test_array = ds2.pixel_array  # fails here because pixel data is too short
    # test_decompression = jpeg_ls.decode(test_array)
    # ds2.PixelData = test_decompression

    # second_decmpn = os.path.join(compression_path, 'second_decmpn.dcm')

    # with open(second_decmpn, 'wb') as writer:
    #     dcmwrite(writer, ds2, write_like_original = False)


def main():
    parent_dir = '/home/jay/projects/dicom/dicom'  # Archive location
    archive = 'MammoTomoUPMC_Case6.tar.bz2'  # Downloaded archive file

    # look_at_download(parent_dir, archive)
    # extract_all_files(parent_dir, archive)

    extracted_archive = 'Case6 [Case6]'  # Name of extracted archive folder
    extracted_path = os.path.join(parent_dir, extracted_archive)

    images_path = make_new_folder(parent_dir, 'Images')
    metadata_path = make_new_folder(parent_dir, 'Metadata')

    # process_for_images(images_path, extracted_path)
    # process_for_metadata(metadata_path, extracted_path)

    compression_path = make_new_folder(parent_dir, 'compression_test')
    example_file = '1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.637.0.dcm'
    example_path = os.path.join(compression_path, example_file)

    # compress_with_dcmtk(compression_path, example_path)
    compress_with_charpyls(compression_path, example_path)


if __name__ == '__main__':
    main()
