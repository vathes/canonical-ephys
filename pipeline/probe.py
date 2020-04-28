import datajoint as dj


# ===================================== Neuropixels Probes =====================================

class ProbeType(dj.Lookup):
    definition = """
    probe_type: varchar(32)  # e.g. neuropixels_1.0
    """

    class Electrode(dj.Part):
        definition = """
        -> master
        electrode: int       # electrode index, starts at 1
        ---
        shank: int           # shank index, starts at 1, advance left to right
        shank_col: int       # column index, starts at 1, advance left to right
        shank_row: int       # row index, starts at 1, advance tip to tail
        x_coord=NULL: float  # (um) x coordinate of the electrode within the probe, (0, 0) is the bottom left corner of the probe
        y_coord=NULL: float  # (um) y coordinate of the electrode within the probe, (0, 0) is the bottom left corner of the probe
        """


class Probe(dj.Lookup):
    definition = """  # represent a physical probe
    probe: varchar(32)  # unique identifier for this model of probe (e.g. part number)
    ---
    -> ProbeType
    probe_comment='' :  varchar(1000)
    """


class ElectrodeConfig(dj.Lookup):
    definition = """
    -> ProbeType
    electrode_config_name: varchar(64)  # user friendly name
    ---
    electrode_config_uuid: uuid     # hash of the group and group_member (ensure uniqueness)
    unique index (electrode_config_hash)
    """

    class Electrode(dj.Part):
        definition = """
        -> master
        -> ProbeType.Electrode
        ---
        is_used: bool  # is this channel used for spatial average (ref channels are by default not used)
        """

