import datajoint as dj
from datetime import datetime
from loaders import neuropixels


def get_ephys_root_data_dir():
    return dj.config.get('custom', {}).get('ephys_data_paths', None)


def get_ephys_probe_data_dir(probe_key):
    root_dir = get_ephys_root_data_dir()

    subj = probe_key['subject_id']
    probe_no = probe_key['insertion_number']
    sess_date_string = probe_key['session_time'].strftime('%m%d%y')

    dir_pattern = f'*{subj}_{sess_date_string}*_imec{probe_no}'
    npx_meta_pattern = f'{subj}_{sess_date_string}*_imec{probe_no}.ap.meta'

    try:
        npx_meta_fp = next(root_dir.rglob('/'.join([dir_pattern, npx_meta_pattern])))
    except StopIteration:
        return None

    npx_meta = neuropixels.NeuropixelsMeta(npx_meta_fp)

    # ensuring time difference between behavior-start and ephys-start is no more than 2 minutes - this is to handle multiple sessions in a day
    start_time_difference = abs((npx_meta.recording_time - probe_key['session_time']).total_seconds())
    if start_time_difference <= 120:
        return npx_meta_fp.parent
