#!usr/bin/env python

"""
Name: Medical Physics DICOM project
Date: 19 Jan 2022
Author: Jay Miles
STP: SBI102 ICT in the Clinical Environment competencies 3 & 4

UPMC Breast Tomography and FFDM Collection:
-www.dclunie.com/pixelmedimagearchive/upmcdigitalmammotomocollection/index.html
-Using Case 6 as an example
-Downloaded file is in .tar.bz2 format and is 172,557 KB
-contains 26 objects - 15 are directories, 11 are uncompressed dcm files
-total file size is 1241286528 bytes
-the files have the element '(7fe0, 0010) Pixel Data', which is a numpy array
-Largest file is 640869820 bytes:
    1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.647.0.dcm
-Smallest file is 3262956 bytes:
    1.3.6.1.4.1.5962.99.1.2280943358.716200484.1363785608958.637.0.dcm

DCM ToolKit (DCMTK)
-Various tools for DCM files, packaged for Ubuntu
-dcmdump can be used to dump DCM file data to text
-dcmcjpls/dcmdjpls can be used to (de)compress in JPEG-LS format
-dcmcrle/dcmdrle can be used to (de)compress in RLE format

pylibjpeg
-Python packages to support image (de)compression via pydicom
-Supports decompression of JPEG, JPEG-LS, JPEG-XT, JPEG2000, RLE formats
-Only supports RLE encoding

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
    """
    Make a new directory and return its path.

    Args:
        parent_dir [path]: path to directory to create new folder in
        name [string]: name of new folder

    Outputs:
        new_dir [path]: path to new folder
    """

    new_dir = os.path.join(parent_dir, name)

    try:
        os.mkdir(new_dir)

    except FileExistsError:
        pass

    return new_dir


def look_at_archive(archive_path):
    """ Use tarfile to examine the contents of a .tar.bz2 archive
    without extracting anything.

    Args:
        archive_path [path]: path to the zipped archive

    Outputs:
        Text descriptions of archive printed to terminal
    """

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
    """ Extract all contents of .tar.bz2 archive.

    Args:
        archive_path [path]: path to the zipped archive

    Outputs:
        Archive contents extracted into current working directory
    """

    tar = tarfile.open(archive_path, 'r:bz2')
    tar.extractall()
    tar.close()


def construct_filename(dcm_filepath, suffix):
    """ For a .dcm file, create a newfilename with a given suffix based
    on the file's dataset elements.

    As the example files used in this script are de-identified and don't
    contain patient names, the last part of the SOPInstanceUID can be
    used as an alternative unique identifier.

    Args:
        dcm_filepath [path]: path to the .dcm file
        suffix [string]: suffix for filename e.g. '.txt', '.png'

    Outputs:
        filename [string]: new filename based on file contents
    """

    # Read in the dataset
    with open(dcm_filepath, 'rb') as reader:
        ds = dcmread(reader)

    # Get details from dataset to construct filename
    image_date = ds['ContentDate'].value
    study_type = ds['StudyDescription'].value
    # pt_name = ds['PatientName']  # use this for actual pt files
    pt_name = ds['SOPInstanceUID'][-7:]  # use this for test files

    # # Determine whether file is single- or multi-frame, or is not an image
    if 'PixelData' in ds:
        if len(ds.pixel_array.shape) == 2:
            frames = 'single_frame'
        elif len(ds.pixel_array.shape) == 3:
            frames = 'multi_frame'

    else:
        frames = 'no_image'

    # Construct the filename string
    filename = '{}_{}_{}_{}{}'.format(
        image_date,
        study_type,
        pt_name,
        frames,
        suffix
        )

    return filename


def compare_dcm_files(filepath_1, filepath_2):
    """ Compare two DICOM files and output the lines where they differ.

    Args:
        filepath_1 [path]: path to a .dcm file
        filepath_2 [path]: path to another .dcm file

    Outputs:
        delta [list]: list of lines which differ between the two files
    """

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

        # Define a list to hold output lines, initialise a Differ() instance
        delta = []
        d = Differ()

        # Compare the elements of rep, store lines which differ between files
        for line in list(d.compare(rep[0], rep[1])):
            if (line[0] == '-') or (line[0] == '+'):
                delta.append(line)

        return delta

    except TypeError as error:
        delta = 'Error whilst comparing files: {}\n\n'.format(error)

        return delta


def decompress_mri_files(input_dir, output_dir):
    """ Take compressed files, decompress and save in new folder.

    Args:
        input_dir [path]: path to directory containing compressed files
        output_dir [path]: path to store decompressed files at

    Outputs:
        Decompressed version created for all compressed .dcm files in
        input directory, stored in output directory
    """

    print('Decompressing files from {}'.format(input_dir))

    # Iterate over a directory and look at .dcm files
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith('anon.dcm'):

                # Get path to original file and define a filename
                filepath = os.path.join(root, file)
                filename = construct_filename(filepath, '.dcm')

                # Read in the original dataset
                with open(filepath, 'rb') as reader:
                    ds = dcmread(reader, force = True)

                try:
                    # Use pylibjpeg to decompress the pixel array
                    ds.decompress('pylibjpeg')

                except NotImplementedError:  # one file is text-only
                    pass

                # Write the updated dataset out to a new file
                output_path = os.path.join(output_dir, filename)

                with open(output_path, 'wb') as writer:
                    dcmwrite(writer, ds, write_like_original = False)


def get_dcm_image(dcm_filepath, new_filename, output_folder):
    """ Given a DICOM file, create a PNG image from its PixelData
    element and save in PNG format in the specified output folder.

    Args:
        dcm_filepath [path]: path to the .dcm file
        output_folder [path]: path to store images at

    Outputs:
        .png image created from PixelData element and stored in output_folder
    """

    # Read in file's dataset and get new filename
    with open(dcm_filepath, 'rb') as reader:
        ds = dcmread(reader)

    # Only continue if file has a PixelData element
    if 'PixelData' in ds:

        # For single-frame files:
        if len(ds.pixel_array.shape) == 2:

            # Create an image
            im = Image.fromarray(np.uint8(ds.pixel_array))

            # Save as .png in the Images directory
            im_filename = '{}.png'.format(new_filename)
            im_path = os.path.join(output_folder, im_filename)
            im.save(im_path)

        # For multiframe files:
        elif len(ds.pixel_array.shape) == 3:

            # Create a new subdirectory to hold the images
            file_dir_path = os.path.join(output_folder, new_filename)

            try:
                os.mkdir(file_dir_path)

            except FileExistsError:
                pass

            # Then create each frame's image in the subdirectory
            i = 1
            for frame in ds.pixel_array:
                im = Image.fromarray(np.uint8(frame))

                im_filename = '{}_{}.png'.format(new_filename, i)
                im_path = os.path.join(file_dir_path, im_filename)
                im.save(im_path)

                i += 1


def get_dcm_text(dcm_filepath, new_filename, output_folder):
    """ Given a path to a .dcm file, use DCMTK's dcmdump to dump the
    file's dataset into a .txt file and save it in the specified output
    folder.

    Args:
        dcm_filepath [path]: path to the .dcm file
        output_folder [path]: path to store text files at

    Outputs:
        .txt file of dataset created and stored in output folder
    """

    # Define output path
    new_filepath = os.path.join(output_folder, new_filename)

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
    folders.

    Args:
        files_dir [path]: path to uncompressed .dcm files
        images_dir [path]: path to store .png outputs at
        metadata_dir [path]:  path to store .txt outputs at

    Outputs:
        .png and .txt files generated for all uncompressed .dcm files
    """

    print('Generating images and text files from {}'.format(files_dir))

    # Iterate over the extracted archive contents
    for root, dirs, files in os.walk(files_dir):

        # Look only at .dcm files
        for file in files:
            if file.lower().endswith('.dcm'):

                # Define the path to the file
                filepath = os.path.join(root, file)

                # Call functions to generate .png and .txt files
                im_filename = construct_filename(filepath, '')
                get_dcm_image(filepath, im_filename, images_dir)

                text_filename = construct_filename(filepath, '.txt')
                get_dcm_text(filepath, text_filename, metadata_dir)


def compress_with_dcmtk(dcm_filepath, output_dir, method):
    """
    Read in a DICOM file at a given filepath
    Perform the specified (de)compression
        -Can compress with 'dcmcjpls' or 'dcmcrle'
        -Can decompress with 'dcmdjpls' or 'dcmdrle'
    Save the (de)compressed file in the specified output folder

    Args:
        dcm_filepath [path]: path to .dcm file
        output_dir [path]: path to store output file at
        method [string]: (de)compression type to use

    Outputs:
        output_path [path]: path to output file
        original_size [integer]: size of original file before (de)compression
        compress_size [integer]: size of file produced by (de)compression
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
        But it can decode various JPEG formats, including JPEG-LS
    Save the resulting file in the specified output folder

    Args:
        dcm_filepath [path]: path to .dcm file
        output_dir [path]: path to store output file at
        method [string]: 'pylibjpeg-compress' or 'pylibjpeg-decompress'

    Outputs:
        output_path [path]: path to output file
        original_size [integer]: size of original file before (de)compression
        compress_size [integer]: size of file produced by (de)compression
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
    Iterate over all uncompressed .dcm files in a directory. Use the
    specified package on each file to compress the dataset and save a
    compressed version of the file. Then use the corresponding
    package/method to decompress the compressed dataset and save a final
    decompressed version of the file. Compare the original file with the
    final decompressed version to determine whether any data is lost and
    whether any element values ahve changed.

    Args:
        files_dir [path]:
        compressed_dir [path]:
        decompressed_dir [path]:
        method [string]: 'dcmtk-jpls', 'dcmtk-rle' or 'pylibjpeg'

    Outputs:
        All files produced during compression and decompression of .dcm files
        .txt file listing changes between original and final decompressed file
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
                    '\nFile: {}\n'
                    'Original file size: {}\n'
                    'Compressed size: {} (-{} bytes, {}-fold change)\n'
                    'Decompressed size: {} (+{})\n'
                    'Data loss: {} bytes\n\n'.format(
                        file,
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
                    writer.write(sentence2)
                    writer.write('Changes between original and final:\n')
                    for line in delta:
                        writer.write(line)


def cross_compression(uncompressed_files, output_dir):
    """
    Iterate over a folder of uncompressed .dcm files. For each one:
            -Perform JPEG-LS Lossless compression using dcmcjpls
            -Create a .txt file from the compressed .dcm

            -Perform JPEG-LS Lossless decompression of the compressed
            file using pylibjpeg
            -Create a .txt file from the decompressed .dcm

            -Compare sizes of original, compressed and decompressed files
            -Compare content of same

    Args:
        uncompressed_files [path]: original files to use
        output_dir [path]: to hold compressed and decompressed files
    """

    print('Running cross-compression on {}'.format(uncompressed_files))

    for root, dirs, files in os.walk(uncompressed_files):
        for file in files:
            if file.lower().endswith('.dcm'):

                filepath = os.path.join(root, file)
                filename = construct_filename(filepath, '')

                # Create compressed file with dcmdjpls

                comp_name = '{}_comp.dcm'.format(filename)
                comp_path = os.path.join(output_dir, comp_name)

                subprocess.run(['dcmcjpls', filepath, comp_path])

                # Create decompressed file with pylibjpeg

                with open(comp_path, 'rb') as reader:
                    ds = dcmread(reader, force = True)

                ds.decompress('pylibjpeg')

                decomp_name = '{}_decomp.dcm'.format(filename)
                decomp_path = os.path.join(output_dir, decomp_name)

                with open(decomp_path, 'wb') as writer:
                    dcmwrite(writer, ds, write_like_original = False)

                # Generate .txt files for both new .dcm files

                comp_text = '{}_comp.txt'.format(filename)
                get_dcm_text(comp_path, comp_text, output_dir)

                decomp_text = '{}_decomp.txt'.format(filename)
                get_dcm_text(decomp_path, decomp_text, output_dir)

                # Compare original, compressed and decompressed file sizes

                original_size = os.path.getsize(filepath)
                comp_size = os.path.getsize(comp_path)
                fold_compression = original_size / comp_size
                decomp_size = os.path.getsize(decomp_path)
                bytes_lost = original_size - decomp_size

                compare_sizes = (
                    '\n\nFilename: {}\n'
                    'Original file: {} bytes\n'
                    'Compressed_file: {} bytes ({}-fold compression)\n'
                    'Decompressed file: {} bytes ({} bytes lost)\n'
                    ).format(
                        filename,
                        original_size,
                        comp_size,
                        fold_compression,
                        decomp_size,
                        bytes_lost
                    )

                # Compare file contents using difflib Differ()

                comp_sentence = '\nOriginal vs compressed file:\n'
                compression = compare_dcm_files(filepath, comp_path)

                decomp_sentence = '\nCompressed vs decompressed file:\n'
                decompression = compare_dcm_files(comp_path, decomp_path)

                net_sentence = '\nOriginal vs decompressed file:\n'
                net_change = compare_dcm_files(filepath, decomp_path)

                # Add comparison info to output text file

                comparison = '{}_comparisons.txt'.format(filename)
                comparison_path = os.path.join(output_dir, comparison)

                with open(comparison_path, 'w') as writer:
                    writer.write(compare_sizes)

                    writer.write(comp_sentence)
                    for line in compression:
                        writer.write(line)

                    writer.write(decomp_sentence)
                    for line in decompression:
                        writer.write(line)

                    writer.write(net_sentence)
                    for line in net_change:
                        writer.write(line)


def main():

    parent_dir = '/home/jay/projects/dicom/dicom'


    """ Look at the compressed archive, extract files """

    # zipped_archive = 'MammoTomoUPMC_Case6.tar.bz2'
    # archive_path = os.path.join(parent_dir, zipped_archive)

    # look_at_archive(archive_path)
    # extract_all_files(archive_path)


    """ Get images and text from initially uncompressed .dcm files """

    # Name and path of folder for all TOMO files
    tomo_dir = 'tomo_breast'
    tomo_files = os.path.join(parent_dir, tomo_dir)

    # Name and path of folder holding original uncompressed TOMO files
    tomo_original_dir = 'tomo_original_uncompressed'
    tomo_original = os.path.join(tomo_files, tomo_original_dir)

    # Make output folders
    tomo_images = make_new_folder(tomo_files, 'tomo_images')
    tomo_text = make_new_folder(tomo_files, 'tomo_text')

    # Generate images and text files
    get_all_images_and_metadata(
        tomo_original,
        tomo_images,
        tomo_text
        )


    """ Get images and text from initially compressed .dcm files """

    # Name and path of folder for all mri files
    mri_dir = 'mri_brain'
    mri_files = os.path.join(parent_dir, mri_dir)

    # Name/path of folder holding original (anonymised) compressed mri files
    mri_original_dir = 'mri_original_anon_compressed'
    mri_original = os.path.join(mri_files, mri_original_dir)

    # Decompress files, store in new folder
    mri_uncompressed = make_new_folder(mri_files, 'mri_uncompressed')
    decompress_mri_files(mri_original, mri_uncompressed)

    # Generate images and text files
    mri_images = make_new_folder(mri_files, 'mri_uncompressed_images')
    mri_text = make_new_folder(mri_files, 'mri_uncompressed_text')

    get_all_images_and_metadata(
            mri_uncompressed,
            mri_images,
            mri_text
            )


    """ Test all different methods of compression/decompression """

    # # Define packages to use for (de)compression
    # options = ['dcmtk-jpls', 'dcmtk-rle', 'pylibjpeg']

    # # Use each package sequentially
    # for method in options:
    #     print('Testing (de)compression with {}'.format(method))

    #     # Create a folder to hold compressed files
    #     compressed_files = make_new_folder(
    #         parent_dir,
    #         'compressed_{}'.format(method)
    #         )

    #     # Create a folder to hold decompressed files
    #     decompressed_files = make_new_folder(
    #         parent_dir,
    #         'decompressed_{}'.format(method)
    #         )

    #     # Run the compression_test function, creates text files to allow
    #     # comparing methods
    #     compression_test(
    #         tomo_files,
    #         compressed_files,
    #         decompressed_files,
    #         method
    #         )


    """ Test cross-compression of files with dcmcjpls and pylibjpeg """

    tomo_x_compression = make_new_folder(parent_dir, 'tomo_x_compression')
    mri_x_compression = make_new_folder(parent_dir, 'mri_x_compression')

    cross_compression(tomo_files, tomo_x_compression)
    cross_compression(mri_uncompressed, mri_x_compression)


if __name__ == '__main__':
    main()
