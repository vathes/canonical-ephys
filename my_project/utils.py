import datajoint as dj


def get_ephys_data_dir():
    return dj.config.get('custom', {}).get('ephys_data_paths', None)


