from os import path
from datetime import datetime
import pandas as pd
import numpy as np
import logging

from .utils import handle_string

log = logging.getLogger(__name__)


class Kilosort:

    ks_files = [
        'params.py',
        'amplitudes.npy',
        'channel_map.npy',
        'channel_positions.npy',
        'pc_features.npy',
        'pc_feature_ind.npy',
        'similar_templates.npy',
        'spike_templates.npy',
        'spike_times.npy',
        'spike_times_sec.npy',
        'spike_times_sec_adj.npy',
        'template_features.npy',
        'template_feature_ind.npy',
        'templates.npy',
        'templates_ind.npy',
        'whitening_mat.npy',
        'whitening_mat_inv.npy',
        'spike_clusters.npy',
        'cluster_groups.csv',
        'cluster_KSLabel.tsv'
    ]

    # keys to self.files, .data are file name e.g. self.data['params'], etc.
    ks_keys = [path.splitext(i)[0] for i in ks_files]

    def __init__(self, dname):
        self._dname = dname
        self._files = {}
        self._data = None
        self._clusters = None

        self._info = {'time_created': datetime.fromtimestamp((dname / 'params.py').stat().st_ctime),
                      'time_modified': datetime.fromtimestamp((dname / 'params.py').stat().st_mtime)}

    @property
    def data(self):
        if self._data is None:
            self._stat()
        return self._data

    @property
    def info(self):
        return self._info

    def _stat(self):
        self._data = {}
        for i in Kilosort.ks_files:
            f = self._dname / i

            if not f.exists():
                log.debug('skipping {} - doesnt exist'.format(f))
                continue

            base, ext = path.splitext(i)
            self._files[base] = f

            if i == 'params.py':
                log.debug('loading params.py {}'.format(f))
                # params.py is a 'key = val' file
                prm = {}
                for line in open(f, 'r').readlines():
                    k, v = line.strip('\n').split('=')
                    prm[k.strip()] = handle_string(v.strip())
                log.debug('prm: {}'.format(prm))
                self._data[base] = prm

            if ext == '.npy':
                log.debug('loading npy {}'.format(f))
                d = np.load(f, mmap_mode='r', allow_pickle=False, fix_imports=False)
                self._data[base] = np.reshape(d, d.shape[0]) if d.ndim == 2 and d.shape[1] == 1 else d

        # Read the Cluster Groups
        if (self._dname / 'cluster_groups.csv').exists():
            df = pd.read_csv(self._dname / 'cluster_groups.csv', delimiter='\t')
            self._data['cluster_groups'] = np.array(df['group'].values)
            self._data['cluster_ids'] = np.array(df['cluster_id'].values)
        elif (self._dname / 'cluster_KSLabel.tsv').exists():
            df = pd.read_csv(self._dname / 'cluster_KSLabel.tsv', sep = "\t", header = 0)
            self._data['cluster_groups'] = np.array(df['KSLabel'].values)
            self._data['cluster_ids'] = np.array(df['cluster_id'].values)
        else:
            raise FileNotFoundError('Neither cluster_groups.csv nor cluster_KSLabel.tsv found!')

    def get_best_channel(self, unit):
        template_idx = self.data['spike_templates'][np.where(self.data['spike_clusters'] == unit)[0][0]]
        chn_templates = self.data['templates'][template_idx, :, :]
        max_chn_idx = np.abs(np.abs(chn_templates).max(axis=0)).argmax()
        max_chn = self.data['channel_map'][max_chn_idx]

        return max_chn, max_chn_idx
