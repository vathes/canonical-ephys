import datajoint as dj
import pathlib
from loaders import neuropixels


def get_ephys_root_data_dir():
    data_dir = dj.config.get('custom', {}).get('ephys_data_dir', None)
    return pathlib.Path(data_dir) if data_dir else None


def get_ephys_probe_data_dir(probe_key):
    root_dir = get_ephys_root_data_dir()

    subj = probe_key['subject_id']
    probe_no = probe_key['insertion_number']
    sess_date_string = probe_key['session_datetime'].strftime('%m%d%y')

    dir_pattern = f'*{subj}_{sess_date_string}*_imec{probe_no}'
    npx_meta_pattern = f'{subj}_{sess_date_string}*_imec{probe_no}.ap.meta'

    try:
        npx_meta_fp = next(root_dir.rglob('/'.join([dir_pattern, npx_meta_pattern])))
    except StopIteration:
        return None

    npx_meta = neuropixels.NeuropixelsMeta(npx_meta_fp)

    # ensuring time difference between behavior-start and ephys-start is no more than 2 minutes - this is to handle multiple sessions in a day
    start_time_difference = abs((npx_meta.recording_time - probe_key['session_datetime']).total_seconds())
    if start_time_difference <= 120:
        return npx_meta_fp.parent


ks2specs = ('mean_waveforms.npy', 'spike_times.npy')  # prioritize QC output, then orig


def get_ks_data_dir(probe_key):
    probe_dir = get_ephys_probe_data_dir(probe_key)

    ks2spec = ks2specs[0] if len(list(probe_dir.rglob(ks2specs[0]))) > 0 else ks2specs[1]
    ks2files = [f.parent for f in probe_dir.rglob(ks2spec)]

    if len(ks2files) > 1:
        raise ValueError('Multiple Kilosort outputs found at: {}'.format([x.as_poxis() for x in ks2files]))

    return ks2files[0]
