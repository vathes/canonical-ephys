import datajoint as dj
import pathlib
import numpy as np
import pandas as pd
import re
from datetime import datetime

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
    npx_meta_pattern = f'{subj}_{sess_date_string}*imec{probe_no}.ap.meta'

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


def extract_clustering_info(cluster_output_dir):
    creation_time = None

    phy_curation_indicators = ['Merge clusters', 'Split cluster', 'Change metadata_group']
    # ---- Manual curation? ----
    phylog_fp = cluster_output_dir / 'phy.log'
    if phylog_fp.exists():
        phylog = pd.read_fwf(phylog_fp, colspecs=[(6, 40), (41, 250)])
        phylog.columns = ['meta', 'detail']
        curation_row = [bool(re.match('|'.join(phy_curation_indicators), str(s))) for s in phylog.detail]
        is_curated = bool(np.any(curation_row))
        if creation_time is None and is_curated:
            row_meta = phylog.meta[np.where(curation_row)[0].max()]
            datetime_str = re.search('\d{2}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}', row_meta)
            if datetime_str:
                creation_time = datetime.strptime(datetime_str.group(), '%Y-%m-%d %H:%M:%S')
            else:
                creation_time = datetime.fromtimestamp(phylog_fp.stat().st_ctime)
                time_str = re.search('\d{2}:\d{2}:\d{2}', row_meta)
                if time_str:
                    creation_time = datetime.combine(creation_time.date(),
                                                     datetime.strptime(time_str.group(), '%H:%M:%S').time())
    else:
        is_curated = False

    # ---- Quality control? ----
    metric_fp = cluster_output_dir / 'metrics.csv'
    if metric_fp.exists():
        is_qc = True
        if creation_time is None:
            creation_time = datetime.fromtimestamp(metric_fp.stat().st_ctime)
    else:
        is_qc = False

    if creation_time is None:
        spk_fp = next(cluster_output_dir.glob('spike_times.npy'))
        creation_time = datetime.fromtimestamp(spk_fp.stat().st_ctime)

    return creation_time, is_curated, is_qc
