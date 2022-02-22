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
-contains 26 objects - 15 are directories, 11 are uncompressed dcm files
-total file size is 1241286528 bytes
-dcm files contain the element '(7fe0, 0010) Pixel Data', which is a numpy array

Largest file is 640869820 bytes:
1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.647.0.dcm

Smallest file is 3262956 bytes:
1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.637.0.dcm

"""


import jpeg_ls  # Actually CharPyLS
import numpy as np
import os
import subprocess
import tarfile

from difflib import Differ
from PIL import Image
from pydicom import dcmread, dcmwrite


def make_new_folder(parent_dir, name):
    """ Make a new directory and return its path """

    new_dir = os.path.join(parent_dir, name)

    try:
        os.mkdir(new_dir)

    except FileExistsError:
        pass

    return new_dir


def look_at_archive(archive_path):
    """ Use tarfile to examine the contents of a .tar.bz2 archive
    without extracting anything. """

    # Open archive
    tar = tarfile.open(archive_path, 'r:bz2')

    # Define counter variables
    object_count = 0
    file_count = 0
    total_size = 0

    largest_file_size = 0
    largest_file = ''

    smallest_file_size = 650000000  # has to be > smallest file size
    smallest_file = ''

    # Iterate over all objects
    for item in tar:

        object_count += 1
        total_size += item.size

        # Print name and size of any regular files
        if item.isreg():
            file_count += 1

            print("File {} is {} bytes.".format(item.name, item.size))

            if item.size > largest_file_size:
                largest_file_size = item.size
                largest_file = item.name

            if item.size < smallest_file_size:
                smallest_file_size = item.size
                smallest_file = item.name

        # Print the name of any directories
        elif item.isdir():
            print("Directory {}".format(item.name))

        else:
            print("{} is not a file or directory.".format(item.name))

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


def extract_all_files(archive_path):
    """ Extract contents of .tar.bz2 archive into current directory """

    tar = tarfile.open(archive_path, 'r:bz2')
    tar.extractall()
    tar.close()


def get_dcm_image(dcm_filepath, output_folder):
    """ Given a DICOM file, create a PNG image from its PixelData
    element and save in PNG format in the specified output folder. """

    # Read in file's dataset

    with open(dcm_filepath, 'rb') as reader:
        ds = dcmread(reader)

    # Construct output filename from dataset elements

    # pt_name = ds['PatientName']  # use this for actual pt files
    pt_name = ds['SOPInstanceUID'][-5:-2]  # use for example files
    image_date = ds['AcquisitionDate'][:]
    image_time = ds['AcquisitionTime'][:-4]

    title = '{}_{}_{}'.format(
        image_date,
        image_time,
        pt_name)

    # Deal with single-frame files
    if len(ds.pixel_array.shape) == 2:

        # Create an image
        im = Image.fromarray(np.uint8(ds.pixel_array))

        # Save as .png in the Images directory
        im_filename = '{}.png'.format(title)
        im_path = os.path.join(output_folder, im_filename)
        im.save(im_path)

    # Deal with multiframe files
    elif len(ds.pixel_array.shape) == 3:

        # Create a new subdirectory to hold the images
        file_dir_path = os.path.join(output_folder, title)

        try:
            os.mkdir(file_dir_path)

        except FileExistsError:
            pass

        i = 1
        for frame in ds.pixel_array:
            im = Image.fromarray(np.uint8(frame))

            im_filename = '{}_frame_{}.png'.format(title, i)
            im_path = os.path.join(file_dir_path, im_filename)
            im.save(im_path)

            i += 1


def get_dcm_metadata(dcm_filepath, output_folder):
    """ Given a DICOM file, use DCMTK's dcmdump to dump its dataset into
    a TXT file and save it in the specified output folder. """

    # Read in the file's dataset

    with open(dcm_filepath, 'rb') as reader:
        ds = dcmread(reader)

    # Construct output filename from dataset elements

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

    new_filepath = os.path.join(output_folder, filename)

    # Run dcmdump via command line to get text output
    dcm_call = ['dcmdump', '-M', str(dcm_filepath)]

    dcm_dump = subprocess.run(
        dcm_call,
        text = True,
        capture_output = True,
        )

    dcm_text = dcm_dump.stdout

    # Write this to a text file
    with open(new_filepath, 'w') as writer:
        writer.write(dcm_text)


def get_all_images_and_metadata(files_dir, images_dir, metadata_dir):
    """ Iterate over a directory containing UNCOMPRESSED .dcm files, and
    generate a .png and .txt file for each in the specified output
    folders. """

    # Iterate over the extracted archive contents
    for root, dirs, files in os.walk(files_dir):

        # Look only at .dcm files
        for file in files:
            if file.lower().endswith('.dcm'):

                # Define the path to the file
                dcm_filepath = os.path.join(root, file)

                # Call functions to generate .png and .txt files
                get_dcm_metadata(dcm_filepath, metadata_dir)
                get_dcm_image(dcm_filepath, images_dir)


def compare_dcm_files(filepath_1, filepath_2):
    """ Compare two DICOM files at the specified paths. """

    datasets = tuple([
        dcmread(path, force=True) for path in (filepath_1, filepath_2)
        ])

    # difflib.compare takes a list of lines, each ending in a newline
    # character

    try:
        rep = []
        for dataset in datasets:
            lines = str(dataset).split("\n")
            lines = [line + "\n" for line in lines]  # add the newlines back in
            rep.append(lines)

        # rep is now a 2-element list, where each element is all lines from
        # a single file

        # Define a list to hold output lines
        delta = []

        # Initialise a Differ() instance
        d = Differ()

        # Compare the two elements of rep, store lines where they differ
        for line in list(d.compare(rep[0], rep[1])):
            if (line[0] == '-') or (line[0] == '+'):
                delta.append(line)

        return delta

    except TypeError:

        return 'Error whilst comparing files.\n\n'


def compress_with_dcmtk(dcm_filepath, compressed_dir, method):
    """ Read in a DICOM file at a given filepath, perform the given
    method of compression ('dcmcjpls' or 'dcmcrle'), and save the
    compressed file in the folder specified by 'compressed_dir'. """

    # Read in the file's dataset (only needed to construct filename)
    with open(dcm_filepath, 'rb') as reader:
        ds = dcmread(reader)

    # Construct output filename from dataset elements

    # pt_name = ds['PatientName']  # use this for actual pt files
    pt_name = ds['SOPInstanceUID'][-5:-2]  # use for example files
    image_date = ds['AcquisitionDate'][:]
    image_time = ds['AcquisitionTime'][:-4]

    if len(ds.pixel_array.shape) == 2:
        frames = 'single_frame'
    elif len(ds.pixel_array.shape) == 3:
        frames = 'multi_frame'

    filename = '{}_{}_{}_{}.dcm'.format(
        image_date,
        image_time,
        pt_name,
        frames,
        )

    output_path = os.path.join(compressed_dir, filename)

    # Create a compressed file using DCMTK's dcmcjpls command
    subprocess.run([method, dcm_filepath, output_path])

    # Compare the original and compressed files
    original_size = os.path.getsize(dcm_filepath)
    compress_size = os.path.getsize(output_path)

    return output_path, original_size, compress_size


def decompress_with_dcmtk(dcm_filepath, decompressed_dir, method):
    """ Read in a DICOM file at a given filepath, perform the given
    method of decompression ('dcmdjpls' or 'dcmdrle'), and save the
    decompressed file in the folder specified by 'decompressed_dir'. """

    # Read in the file's dataset (only needed to construct filename)
    with open(dcm_filepath, 'rb') as reader:
        ds = dcmread(reader)

    # Construct output filename from dataset elements

    # pt_name = ds['PatientName']  # use this for actual pt files
    pt_name = ds['SOPInstanceUID'][-5:-2]  # use for example files
    image_date = ds['AcquisitionDate'][:]
    image_time = ds['AcquisitionTime'][:-4]

    if len(ds.pixel_array.shape) == 2:
        frames = 'single_frame'
    elif len(ds.pixel_array.shape) == 3:
        frames = 'multi_frame'

    filename = '{}_{}_{}_{}.dcm'.format(
        image_date,
        image_time,
        pt_name,
        frames,
        )

    output_path = os.path.join(decompressed_dir, filename)

    # Create a compressed file using DCMTK's dcmcjpls command
    subprocess.run([method, dcm_filepath, output_path])

    # Compare the original and compressed files
    decompress_size = os.path.getsize(output_path)

    return output_path, decompress_size


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


def compression_test(files_dir, compressed_dir, decompressed_dir):
    """ Iterate over .dcm files in the specified directory. For each
    file:

    -Compress it using dcmcjpls and save to folder of compressed files.
    -Decompress the compressed file with dcmdjpls and save to folder of
    decompressed files.
    -Compare the original and decompressed files to evaluate data loss.
    """

    compress_method = 'dcmcjpls'  # options: 'dcmcjpls' or 'dcmcrle'
    decompress_method = 'dcmdjpls'  # options: 'dcmdjpls' or 'dcmdrle'
    text_file = 'compression_test_{}.txt'.format(compress_method)

    sentence1 = 'Testing (de)compression with {}/{}\n\n'.format(
        compress_method,
        decompress_method
        )

    with open(text_file, 'w') as writer:
        writer.write(sentence1)

    # Iterate over the extracted archive contents
    for root, dirs, files in os.walk(files_dir):

        # Look only at .dcm files
        for file in files:
            if file.lower().endswith('.dcm'):

                print(file)

                # Define the path to the file
                dcm_filepath = os.path.join(root, file)

                # Compress original file and save
                (compressed_file,  # path to compressed file
                original_size,
                compress_size) = compress_with_dcmtk(
                    dcm_filepath,
                    compressed_dir,
                    compress_method
                    )

                # Decompress compressed file and save
                (decompressed_file,  # path to decompressed file
                decompress_size) = decompress_with_dcmtk(
                    compressed_file,
                    decompressed_dir,
                    decompress_method
                    )

                # Identify data loss
                compression = original_size - compress_size
                decompression = decompress_size - compress_size
                data_loss = original_size - decompress_size

                sentence2 = '\nOriginal file size: {}\nCompressed size: {} (-{})\nDecompressed size: {} (+{})\nData loss: {} bytes\n\n'.format(original_size, compress_size, compression, decompress_size, decompression, data_loss)

                # List differences between original and final file
                delta = compare_dcm_files(
                    dcm_filepath,
                    decompressed_file
                    )

                # Append to test output text
                with open(text_file, 'a') as writer:
                    writer.write('\n{}\n'.format(file))
                    writer.write(sentence2)
                    for line in delta:
                        writer.write(line)


def main():
    parent_dir = '/home/jay/projects/dicom/dicom'  # Archive location
    archive = 'MammoTomoUPMC_Case6.tar.bz2'  # Archive name
    extracted_archive = 'Case6 [Case6]'  # Extracted folder name

    """ Look at the compressed archive, extract files """

    archive_path = os.path.join(parent_dir, archive)
    # look_at_archive(archive_path)
    # extract_all_files(archive_path)

    """ Get metadata and images from DICOM files """

    original_files = os.path.join(parent_dir, extracted_archive)

    # # Create new directories to hold the output
    # original_images = make_new_folder(parent_dir, 'original_images')
    # original_metadata = make_new_folder(parent_dir, 'original_metadata')

    # # Generate image/text files from DICOM files
    # get_all_images_and_metadata(
    #     original_files,
    #     original_images,
    #     original_metadata
    #     )

    """ Compress and decompress DICOM files """

    # Create new directories to hold the output
    compressed_files = make_new_folder(parent_dir, 'compressed_files')

    decompressed_files = make_new_folder(
        parent_dir,
        'decompressed_files'
        )

    # Compress all DICOM files, then decompress and look at data loss
    compression_test(
        original_files,
        compressed_files,
        decompressed_files
        )


if __name__ == '__main__':
    main()
