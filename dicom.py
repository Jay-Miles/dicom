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

Compression and decompression using DCMTK results in some data loss.
Compression and decompression using pylibjpeg results in no data loss.

JPEG-LS compression via dcmcjpls gives the greatest compression.
Compression with pylibjpeg is slightly more than with dcmcrle.

"""


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


def construct_filename(dcm_filepath, suffix):
    """ Given a path to a .dcm file, create a filename with a given
    suffix (e.g. '.txt', '.png') based on the file's dataset elements.

    As the example files are de-identified and don't contain patient
    names, use the last part of the SOPInstanceUID as a unique
    identifier for these.
    """

    # Read in the dataset
    with open(dcm_filepath, 'rb') as reader:
        ds = dcmread(reader)

    # Get the image acquisition date and time, and the patient name
    image_date = ds['AcquisitionDate'][:]
    image_time = ds['AcquisitionTime'][:-4]
    # pt_name = ds['PatientName']  # use this for actual pt files
    pt_name = ds['SOPInstanceUID'][-5:-2]  # use for example files

    # Determine whether file is single- or multi-frame
    if len(ds.pixel_array.shape) == 2:
        frames = 'single_frame'
    elif len(ds.pixel_array.shape) == 3:
        frames = 'multi_frame'

    # Construct the filename string
    filename = '{}_{}_{}_{}{}'.format(
        image_date,
        image_time,
        pt_name,
        frames,
        suffix
        )

    return filename


def get_dcm_image(dcm_filepath, output_folder):
    """ Given a DICOM file, create a PNG image from its PixelData
    element and save in PNG format in the specified output folder. """

    # Read in file's dataset and get new filename
    with open(dcm_filepath, 'rb') as reader:
        ds = dcmread(reader)

    filename = construct_filename(dcm_filepath, '')

    # For single-frame files:
    if len(ds.pixel_array.shape) == 2:

        # Create an image
        im = Image.fromarray(np.uint8(ds.pixel_array))

        # Save as .png in the Images directory
        im_filename = '{}.png'.format(filename)
        im_path = os.path.join(output_folder, im_filename)
        im.save(im_path)

    # For multiframe files:
    elif len(ds.pixel_array.shape) == 3:

        # Create a new subdirectory to hold the images
        file_dir_path = os.path.join(output_folder, filename)

        try:
            os.mkdir(file_dir_path)

        except FileExistsError:
            pass

        i = 1
        for frame in ds.pixel_array:
            im = Image.fromarray(np.uint8(frame))

            im_filename = '{}_{}.png'.format(filename, i)
            im_path = os.path.join(file_dir_path, im_filename)
            im.save(im_path)

            i += 1


def get_dcm_metadata(dcm_filepath, output_folder):
    """ Given a path to a .dcm file, use DCMTK's dcmdump to dump the
    file's dataset into a .txt file and save it in the specified output
    folder. """

    # Get new filename and define output path
    filename = construct_filename(dcm_filepath, '.txt')
    new_filepath = os.path.join(output_folder, filename)

    # Run dcmdump via command line to get text version of file
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
    """ Compare two DICOM files at the specified paths, output the lines
    on which they differ. """

    # difflib.compare needs a list of lines, each ending in a newline

    datasets = tuple([
        dcmread(path, force=True) for path in (filepath_1, filepath_2)
        ])

    try:
        rep = []
        for dataset in datasets:
            lines = str(dataset).split("\n")  # split into separate lines
            lines = [line + "\n" for line in lines]  # add newline chars back
            rep.append(lines)

        # 'rep' is now a 2-element list, where each element is a list of all
        # lines from a single file

        # Define a list to hold output lines
        delta = []

        # Initialise a Differ() instance
        d = Differ()

        # Compare the elements of rep, store lines which differ between files
        for line in list(d.compare(rep[0], rep[1])):
            if (line[0] == '-') or (line[0] == '+'):
                delta.append(line)

        return delta

    except TypeError as error:
        sentence = 'Error whilst comparing files: {}\n\n'.format(error)

        return sentence


def compress_with_dcmtk(dcm_filepath, output_dir, method):
    """
    Read in a DICOM file at a given filepath
    Perform the specified (de)compression
        -Can compress with 'dcmcjpls' or 'dcmcrle'
        -Can decompress with 'dcmdjpls' or 'dcmdrle'
    Save the (de)compressed file in the specified output folder
    """

    # Define new filename and output path
    filename = construct_filename(dcm_filepath, '.dcm')
    output_path = os.path.join(output_dir, filename)

    # Convert the file using DCMTK's dcmcjpls command
    subprocess.run([method, dcm_filepath, output_path])

    # Compare the original and compressed files
    original_size = os.path.getsize(dcm_filepath)
    compress_size = os.path.getsize(output_path)

    return output_path, original_size, compress_size


def compress_with_pylibjpeg(dcm_filepath, output_dir, method):
    """
    Read in a DICOM file at a given filepath
    Use pylibjpeg to (de)compress it
        Note that the ONLY encoding capability pylibjpeg has is RLE
        (But it can decode with JPEG-LS)
    Save the resulting file in the specified output folder
    """

    # Read in the original dataset and define name for new file
    with open(dcm_filepath, 'rb') as reader:
        ds = dcmread(reader, force = True)

    filename = construct_filename(dcm_filepath, '.dcm')

    # Perform compression with pylibjpeg-rle (only encoding available)
    if method == 'pylibjpeg-compress':
        ds.compress('1.2.840.10008.1.2.5')  # RLE Lossless

    # Or perform decompression (can decode various TransferSyntaxUIDs)
    elif method == 'pylibjpeg-decompress':
        ds.decompress('pylibjpeg')

    # Write the updated dataset out to a new file
    output_path = os.path.join(output_dir, filename)

    with open(output_path, 'wb') as writer:
        dcmwrite(writer, ds, write_like_original = False)

    # Compare the original and decompressed file sizes
    original_size = os.path.getsize(dcm_filepath)
    compress_size = os.path.getsize(output_path)

    return output_path, original_size, compress_size


def compression_test(files_dir, compressed_dir, decompressed_dir, method):
    """
    Iterate over .dcm files in the specified directory
    For each file:
        Using the specified method,
        Compress the dataset and save to a folder of compressed files
        Decompress the compressed file and save to another folder
        Produce a text file describing file size/content changes
    """

    # Initialise the output text file
    text_file = 'compression_test_{}.txt'.format(method)
    sentence1 = 'Testing (de)compression with {}\n'.format(method)

    with open(text_file, 'w') as writer:
        writer.write(sentence1)

    # Iterate over the directory contents
    for root, dirs, files in os.walk(files_dir):

        # Look only at .dcm files
        for file in files:
            if file.lower().endswith('.dcm'):

                print(file)

                # Define the path to the file
                dcm_filepath = os.path.join(root, file)

                # USING DCMTK
                if (method == 'dcmtk-jpls') or (method == 'dcmtk-rle'):

                    # DCMTK: JPEG-LS Lossless
                    if method == 'dcmtk-jpls':
                        compress_method = 'dcmcjpls'
                        decompress_method = 'dcmdjpls'

                    # DCMTK: RLE Lossless
                    elif method == 'dcmtk-rle':
                        compress_method = 'dcmcrle'
                        decompress_method = 'dcmdrle'

                    # Compression

                    (compressed_file,  # path to output file
                    original_size,  # size of original file
                    compress_size  # size after compression
                    ) = compress_with_dcmtk(
                        dcm_filepath,  # path to original file
                        compressed_dir,  # output directory
                        compress_method  # method of compression to use
                        )

                    # Decompression

                    (decompressed_file,  # path to output file
                    compress_size,  # size before decompression
                    decompress_size  # size after decompression
                    ) = compress_with_dcmtk(
                        compressed_file,  # path to input file
                        decompressed_dir,  # output directory
                        decompress_method  # method of decompression to use
                        )

                # USING PYLIBJPEG
                elif method == 'pylibjpeg':

                    # Compression

                    (compressed_file,
                    original_size,
                    compress_size) = compress_with_pylibjpeg(
                        dcm_filepath,
                        compressed_dir,
                        'pylibjpeg-compress'
                        )

                    # Decompression

                    (decompressed_file,
                    compress_size,
                    decompress_size) = compress_with_pylibjpeg(
                        compressed_file,
                        decompressed_dir,
                        'pylibjpeg-decompress'
                        )

                # Compare file sizes to identify data loss
                compression = original_size - compress_size
                fold_compression = round(original_size / compress_size, 2)
                decompression = decompress_size - compress_size
                data_loss = original_size - decompress_size

                sentence2 = (
                    '\nOriginal file size: {}\n'
                    'Compressed size: {} (-{} bytes, {}-fold change)\n'
                    'Decompressed size: {} (+{})\n'
                    'Data loss: {} bytes\n\n'.format(
                        original_size,
                        compress_size,
                        compression,
                        fold_compression,
                        decompress_size,
                        decompression,
                        data_loss))

                # List differences between original and final file
                delta = compare_dcm_files(
                    dcm_filepath,
                    decompressed_file
                    )

                # Add information to the output text file
                with open(text_file, 'a') as writer:
                    writer.write('\n{}\n'.format(file))
                    writer.write(sentence2)
                    writer.write('Altered lines:\n')
                    for line in delta:
                        writer.write(line)


def main():
    parent_dir = '/home/jay/projects/dicom/dicom'  # Path to downloaded archive
    archive = 'MammoTomoUPMC_Case6.tar.bz2'  # Archive name
    extracted_archive = 'Case6 [Case6]'  # Extracted directory name

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

    # # Create new directories to hold the output
    # compressed_files = make_new_folder(parent_dir, 'compressed_files')
    # decompressed_files = make_new_folder(parent_dir, 'decompressed_files')

    # # Test various methods of compression/decompression
    # # options: 'dcmtk-jpls', 'dcmtk-rle', 'pylibjpeg'
    # method = 'pylibjpeg'

    # compression_test(
    #     original_files,
    #     compressed_files,
    #     decompressed_files,
    #     method
    #     )


if __name__ == '__main__':
    main()
