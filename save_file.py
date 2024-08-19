import json
from tempfile import NamedTemporaryFile
import zipfile

import numpy


def write_archive(metadata : dict, source_data_name : str, dest_archive : str):
    with zipfile.ZipFile(dest_archive, 'w',
                        compression=zipfile.ZIP_DEFLATED,
                        compresslevel=6) as archive_file:
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