import datajoint as dj
from pipeline import probe
from lab_management import lab


# ===================================== Specify "upstream" tables =====================================

Subject = lab.Subject
Session = lab.Session
Location = lab.Location

# ===================================== Probe Insertion =====================================


class ProbeInsertionAcute(dj.Manual):  # choice 1 (acute)

    _Subject = Subject
    _Session = Session

    definition = """
    -> self._Subject  # API hook point
    -> self._Session  # API hook point
    insertion_number: int
    ---
    -> probe.Probe
    """


class ProbeInsertionChronic(dj.Manual):  # choice 2 (chronic)

    _Subject = Subject

    definition = """
    -> self._Subject  # API hook point
    insertion_number: int
    ---
    -> probe.Probe
    insertion_time: datetime
    """

ProbeInsertion = ProbeInsertionAcute

# ===================================== Insertion Location =====================================


class InsertionLocation(dj.Manual):

    _ProbeInsertion = ProbeInsertion
    _Location = Location

    definition = """
    -> self._ProbeInsertion      # API hook point
    -> self._Location            # API hook point
    """


# ===================================== Ephys Recording =====================================


class EphysRecording(dj.Manual):

    _Session = Session
    _ProbeInsertion = ProbeInsertion
    _get_npx_data_dir = ...

    definition = """
    -> self._Session             # API hook point
    -> self._ProbeInsertion      # API hook point
    ---
    -> probe.ElectrodeConfig
    """


# ===================================== Ephys LFP =====================================

class LFP(dj.Imported):
    definition = """
    -> EphysRecording
    ---
    lfp_sample_rate: float          # (Hz)
    lfp_time_stamps: longblob       # timestamps with respect to the start of the recording (recording_timestamp)
    lfp_mean: longblob              # mean of LFP across electrodes - shape (time,)
    """

    class Electrode(dj.Part):
        definition = """
        -> master
        -> probe.ElectrodeConfig.Electrode  
        ---
        lfp: longblob               # recorded lfp at this electrode
        """

# ===================================== Clustering =====================================


class ClusteringMethod(dj.Lookup):
    definition = """
    clustering_method: varchar(32)
    ---
    clustering_method_desc: varchar(1000)
    """

    contents = zip(['kilosort'])


class ClusterQualityLabel(dj.Lookup):
    definition = """
    # Quality
    cluster_quality_label  :  varchar(100)
    ---
    cluster_quality_description :  varchar(4000)
    """
    contents = [
        ('good', 'single unit'),
        ('ok', 'probably a single unit, but could be contaminated'),
        ('mua', 'multi-unit activity'),
        ('noise', 'bad unit')
    ]


class Clustering(dj.Manual):

    _get_ks_data_dir = ...

    definition = """
    -> EphysRecording
    clustering_instance: uuid
    ---
    -> ClusteringMethod
    clustering_time: datetime  # time of generation of this set of clustering results 
    quality_control: bool  # has this clustering result undergone quality control?
    manual_curation: bool  # has manual curation been performed on this clustering result?
    clustering_note='': varchar(2000)  
    """


# class ChampionClustering


class Unit(dj.Imported):
    definition = """   
    -> Clustering
    unit: int
    ---
    -> probe.ElectrodeConfig.Electrode  # electrode on the probe that this unit has highest response amplitude
    -> ClusterQualityLabel
    """


class UnitSpikeTimes(dj.Imported):
    """
    Extracting unit spike times per recording - relies on the clustering routine
        outputting spikes with times relative to the start of the earliest Session in this SessionGroup
    """
    definition = """
    -> Unit
    ---
    spike_count: int              # how many spikes in this recording of this unit
    unit_spike_times: longblob    # (s) spike times of this unit, relative to the start of the EphysRecording
    """


class Waveform(dj.Imported):
    definition = """
    -> Unit
    """

    class Electrode(dj.Part):
        definition = """
        -> master
        -> probe.ElectrodeConfig.Electrode  
        --- 
        waveform_mean: longblob   # mean over all spikes
        waveforms=null: longblob  # (spike x sample) waveform of each spike at each electrode
        """


# ===================================== Quality Control =====================================


class ClusterQualityMetrics(dj.Imported):
    definition = """
    -> Unit
    ---
    amp: float
    snr: float
    isi_violation: float
    firing_rate: float

    presence_ratio: float  # Fraction of epoch in which spikes are present
    amplitude_cutoff: float  # Estimate of miss rate based on amplitude histogram
    isolation_distance=null: float  # Distance to nearest cluster in Mahalanobis space
    l_ratio=null: float  # 
    d_prime=null: float  # Classification accuracy based on LDA
    nn_hit_rate=null: float  # 
    nn_miss_rate=null: float
    silhouette_score=null: float  # Standard metric for cluster overlap
    max_drift=null: float  # Maximum change in spike depth throughout recording
    cumulative_drift=null: float  # Cumulative change in spike depth throughout recording 

    """