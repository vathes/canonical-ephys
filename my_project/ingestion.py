import re
import uuid

from loaders import neuropixels
from my_project.lab_management import lab
from my_project.init_ephys import ephys_tbls
from my_project.utils import get_ephys_root_data_dir, get_ks_data_dir, extract_clustering_info

from pipeline.utils import dict_to_hash

# ========== Insert new "Subject" ===========

subjects = [{'subject_id': 'dl36', 'sex': 'F', 'dob': '2019-05-06 03:20:01'},
            {'subject_id': 'dl40', 'sex': 'M', 'dob': '2019-07-09 03:20:01'},
            {'subject_id': 'dl56', 'sex': 'F', 'dob': '2019-12-11 03:20:01'},
            {'subject_id': 'dl59', 'sex': 'F', 'dob': '2019-03-16 03:20:01'},
            {'subject_id': 'dl62', 'sex': 'M', 'dob': '2019-05-26 03:20:01'},
            {'subject_id': 'SC011', 'sex': 'M', 'dob': '2019-01-06 03:20:01'},
            {'subject_id': 'SC017', 'sex': 'M', 'dob': '2019-08-01 03:20:01'},
            {'subject_id': 'SC022', 'sex': 'M', 'dob': '2019-09-02 03:20:01'},
            {'subject_id': 'SC030', 'sex': 'F', 'dob': '2019-10-19 03:20:01'},
            {'subject_id': 'SC031', 'sex': 'F', 'dob': '2019-12-11 03:20:01'},
            {'subject_id': 'SC035', 'sex': 'F', 'dob': '2019-02-16 03:20:01'},
            {'subject_id': 'SC038', 'sex': 'F', 'dob': '2019-04-26 03:20:01'}]

lab.Subject.insert(subjects, skip_duplicates=True)

# ========== Insert new "Session" ===========
data_dir = get_ephys_root_data_dir()

sessions = []
for subj_key in lab.Subject.fetch('KEY'):
    subj_dir = data_dir / subj_key['subject_id']
    if subj_dir.exists():
        try:
            meta_filepath = next(subj_dir.rglob('*.ap.meta'))
        except StopIteration:
            continue

        npx_meta = neuropixels.NeuropixelsMeta(meta_filepath)
        sessions.append({**subj_key, 'session_datetime': npx_meta.recording_time})

lab.Session.insert(sessions, skip_duplicates=True)


# ========== Insert new "ProbeInsertion" ===========
ProbeInsertion = ephys_tbls['ProbeInsertionAcute']
Probe = ephys_tbls['Probe']

probe_insertions = []
for sess_key in lab.Session.fetch('KEY'):
    subj_dir = data_dir / sess_key['subject_id']
    if subj_dir.exists():
        for meta_filepath in subj_dir.rglob('*.ap.meta'):
            npx_meta = neuropixels.NeuropixelsMeta(meta_filepath)

            probe = {'probe_type': npx_meta.probe_model, 'probe': npx_meta.probe_SN}
            Probe.insert1(probe, skip_duplicates=True)

            probe_dir = meta_filepath.parent
            probe_number = re.search('(imec)?\d{1}$', probe_dir.name).group()
            probe_number = int(probe_number.replace('imec', '')) if 'imec' in probe_number else int(probe_number)

            probe_insertions.append({**sess_key, **probe, 'insertion_number': int(probe_number)})

ProbeInsertion.insert(probe_insertions, ignore_extra_fields=True, skip_duplicates=True)

# ========== Insert new "Clustering" ===========

EphysRecording = ephys_tbls['EphysRecording']
Clustering = ephys_tbls['Clustering']

clusterings = []
for ephys_key in EphysRecording.fetch('KEY'):
    ks_dir = get_ks_data_dir(ephys_key)
    creation_time, is_curated, is_qc = extract_clustering_info(ks_dir)

    clus_key = {**ephys_key,
                'clustering_method': 'kilosort',
                'clustering_time': creation_time,
                'quality_control': is_qc,
                'manual_curation': is_curated}

    clus_uuid = uuid.UUID(dict_to_hash(clus_key))

    clusterings.append({**clus_key, 'clustering_instance': clus_uuid})

Clustering.insert(clusterings, skip_duplicates=True)
