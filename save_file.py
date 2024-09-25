import json
from tempfile import NamedTemporaryFile
import zipfile
import os

from numpy.typing import NDArray



def write_archive(metadata : dict, source_data_name : str, dest_archive : str):
    metadata['description'] = ("Data recorded from a data gathering session, "
    "can be found inside data.bin file. It is a binary file that consists of "
    "oscilloscope readouts concatenated one after the other. To read this file "
    "you can use numpy -> 'numpy.fromfile()' and than reshape it -> "
    "'.reshape((-1, <record_length>))'. record_length can be found in this "
    "metadata file.")
    with zipfile.ZipFile(dest_archive, 'w',
                        compression=zipfile.ZIP_DEFLATED,
                        compresslevel=9) as archive_file:
        with NamedTemporaryFile('w') as metadata_file:
            metadata_file.write(json.dumps(metadata, indent=4))
            metadata_file.flush()
            archive_file.write(metadata_file.name, 'metadata.txt')
        archive_file.write(source_data_name, 'data.bin')

    print('Data Saved in:', dest_archive)
    os.remove(source_data_name)

def write_archive_xy(metadata           : dict,
                     x_data_array,
                     y_data_file_path   : str,
                     dest_archive       : str):
    """Writes metadata x and y values of the scope into a compressed zip archive.

    Args:
        metadata (dict): metadata dictionary with generator/osciloscope info
        x_data_array (ndarray): array of x values of osciloscope (time)
        y_data_file_path (str): path to binary file with y data
        dest_archive (str): path to destination archive
    """
    metadata['description'] = ("Data recorded from a data gathering session, "
    "can be found inside data.bin file. It is a binary file that consists of "
    "oscilloscope readouts concatenated one after the other. To read this file "
    "you can use numpy -> 'numpy.fromfile()' and than reshape it -> "
    "'.reshape((-1, <record_length>))'. record_length can be found in this "
    "metadata file.")
    # with SpooledTemporaryFile() as namedTempArchive:
    with zipfile.ZipFile(dest_archive, 'w',
                        compression=zipfile.ZIP_DEFLATED,
                        compresslevel=9) as archive_file:
        directory=os.path.basename(dest_archive).split('.')[0]
        archive_file.mkdir(directory)


        # Write metadata into 'metadata.txt'
        archive_file.writestr(
            os.path.join(directory, 'metadata.txt'),
            json.dumps(metadata, indent=4)
        )

        # Write x data into 'xdata.csv'
        archive_file.writestr(
            os.path.join(directory, 'xdata.csv'),
            '\n'.join(str(x) for x in x_data_array)
        )

        # Write y data to archive from y_data_file_path
        archive_file.write(
            y_data_file_path,
            os.path.join(directory, 'ydata.bin')
        )

    print('Data Saved in:', dest_archive)
    os.remove(y_data_file_path)

def append_binary_file(dest_file : str, data : NDArray):
        # write y-vals of the waveform into file
        with open(dest_file, 'ab') as file:
            file.write(data.tobytes())