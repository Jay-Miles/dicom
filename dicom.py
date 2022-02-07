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
                    im_filename = filename + '.png'
                    im_path = os.path.join(images_path, im_filename)

                    im.save(im_path)

                # Deal with multiframe files
                if len(image_array.shape) == 3:

                    # Create a new subdirectory to hold the images
                    file_dir_path = os.path.join(images_path, filename)

                    try:
                        os.mkdir(file_dir_path)

                    except FileExistsError:
                        continue

                    i = 1
                    for frame in image_array:
                        im = Image.fromarray(np.uint8(frame))

                        im_filename = '{}_{}.png'.format(filename, i)
                        im_path = os.path.join(file_dir_path, im_filename)
                        im.save(im_path)

                        i += 1


def process_for_metadata(metadata_path, extracted_path):
    """ Iterate over the contents of a directory and dump the metadata
    for each .dcm file """

    # Iterate over the extracted archive contents
    for root, dirs, files in os.walk(extracted_path):

        # Look only at files
        for file in files:

            # Look only at .dcm files
            if file.lower().endswith('.dcm'):

                # Use dcmdump to output the file contents
                old_filepath = os.path.join(root, file)
                new_filename = file[:-4] + '.txt'
                new_filepath = os.path.join(metadata_path, new_filename)

                dcm_call = ['dcmdump', '-M', str(old_filepath)]

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
    for data loss. Uses RLELossLess and definitely loses data """

    # Define the file to use
    original_file = example_path
    original_file_size = os.path.getsize(original_file)
    print('Original file size: {}'.format(original_file_size))

    # Create a compressed RLELossLess file with dcmtk
    compressed_file = os.path.join(
        compression_path,
        'after_compression.dcm'
        )

    compress_command = ['dcmcrle', original_file, compressed_file]
    subprocess.run(compress_command)

    # Look at the compressed file size
    compressed_file_size = os.path.getsize(compressed_file)
    print('Compressed file size: {}'.format(compressed_file_size))

    # Create a re-decompressed file with dcmtk
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
    """ compress and then decompress an example .dcm file with the
    CharPyLS package """

    # Define the file to use and read in data
    original_file_size = os.path.getsize(example_path)
    print('Original file size: {}'.format(original_file_size))

    with open(example_path, 'rb') as reader:
        ds = dcmread(reader)

    original_array = ds.pixel_array

    # Check the values of specified fields are suitable for JPEGLSLossLess TSUID
    fields = [
        ('PhotometricInterpretation', ['MONOCHROME1', 'MONOCHROME2']),
        ('TransferSyntaxUID', ['any']),
        ('SamplesPerPixel', ['1']),
        ('PlanarConfiguration', ['absent']),
        ('PixelRepresentation', ['0', '1']),
        ('BitsAllocated', ['8', '16']),
        ('BitsStored', [str(number) for number in range(2, 17)]),
        ('HighBit', [str(number) for number in range(1, 16)]),
        ]

    not_in_ds = []

    for field in fields:
        try:
            field_name = field[0]
            print(ds[field_name])

        except KeyError:
            not_in_ds.append(field[0])

    print('Fields not in dataset: {}'.format(not_in_ds))

    # Compress pixel array with CharPyLS and replace PixelData
    compressed_array = jpeg_ls.encode(original_array)
    ds.PixelData = compressed_array

    # Change the necessary data elements
    ds.file_meta.TransferSyntaxUID = 'JPEG​LS​Lossless'
    # ds.is_little_endian =
    # ds.is_implicit_VR =

    # Write the modified dataset to a file
    compressed_file = os.path.join(
        compression_path,
        'after_compression.dcm'
        )

    with open(compressed_file, 'wb') as writer:
        ds.write(writer, write_like_original = False)

    # Look at the compressed file size
    compressed_file_size = os.path.getsize(compressed_file)
    print('Compressed file size: {}'.format(compressed_file_size))

    # # Create a re-decompressed file with dcmtk
    # decompressed_file = os.path.join(
    #     compression_path,
    #     'after_decompression.dcm'
    #     )

    # # Look at the decompressed file size
    # decompressed_file_size = os.path.getsize(decompressed_file)
    # print('Decompressed file size: {}'.format(decompressed_file_size))


def main():
    parent_dir = '/home/jay/projects/dicom/dicom'  # Archive location
    archive = 'MammoTomoUPMC_Case6.tar.bz2'  # Downloaded archive file
    extracted_archive = 'Case6 [Case6]'  # Name of extracted archive folder

    extracted_path = os.path.join(parent_dir, extracted_archive)
    images_path = make_new_folder(parent_dir, 'Images')
    metadata_path = make_new_folder(parent_dir, 'Metadata')
    compression_path = make_new_folder(parent_dir, 'compression_test')

    example_file = '1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.637.0.dcm'
    example_path = os.path.join(compression_path, example_file)

    # look_at_download(parent_dir, archive)
    # extract_all_files(parent_dir, archive)
    # process_for_images(images_path, extracted_path)
    # process_for_metadata(metadata_path, extracted_path)

    # compress_with_dcmtk(compression_path, example_path)
    compress_with_charpyls(compression_path, example_path)


if __name__ == '__main__':
    main()
