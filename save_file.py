import json
from tempfile import NamedTemporaryFile
import zipfile

import numpy


def write_archive(metadata : dict, source_data_name : str, dest_archive : str):
    metadata['descriptnion'] = '''Data recorded from a data gathering session,
    can be found inside data.bin file. It is a binary file that consists of
    oscilloscope readouts concatenated one after the other. To read this file
    you can use numpy -> `numpy.fromfile()` and than reshape it ->
    '.reshape((-1, <record_length>))'. record_length can be found in this
    metadata file.'''
    with zipfile.ZipFile(dest_archive, 'w',
                        compression=zipfile.ZIP_DEFLATED,
                        compresslevel=9) as archive_file:
        with NamedTemporaryFile('w') as metadata_file:
            metadata_file.write(json.dumps(metadata, indent=4))
            metadata_file.flush()
            archive_file.write(metadata_file.name, 'metadata.txt')
        archive_file.write(source_data_name, 'data.bin')

    print('Data Saved in:', dest_archive)

def append_binary_file(dest_file : str, data : numpy.array):
        # write y-vals of the waveform into file
        with open(dest_file, 'ab') as file:
            file.write(data.tobytes())