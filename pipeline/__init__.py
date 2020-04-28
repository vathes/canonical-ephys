from .ephys import *
from .probe import *


# ========================== HELPER METHODS =======================

probe_tbls = (ProbeType, Probe, ElectrodeConfig)

config_tbls = (ProbeInsertion, InsertionLocation, EphysRecording)

non_config_tbls = (LFP, ClusteringMethod, ClusterQualityLabel, Clustering, Unit, UnitSpikeTimes, Waveform)


def _init_probe_tbls(schema, context):
    init_tbls = {}
    for tbl in probe_tbls:
        print(f'Initializing {tbl.__name__}')
        init_tbl = schema(tbl, context=context)
        context[tbl.__name__] = init_tbl
        init_tbls[tbl.__name__] = init_tbl

    return init_tbls


def _init_config_tbls(schema, subject, session, location, context):
    init_tbls = {}
    for tbl in config_tbls:
        for hook_target, hook_name in zip((subject, session, location), ('_Subject', '_Session', '_Location')):
            if hook_name in dir(tbl):
                setattr(tbl, hook_name, hook_target)

        print(f'Initializing {tbl.__name__}')
        init_tbl = schema(tbl, context=context)
        context[tbl.__name__] = init_tbl
        init_tbls[tbl.__name__] = init_tbl

    return init_tbls


def _init_nonconfig_tbls(schema, context):
    init_tbls = {}
    for tbl in non_config_tbls:
        print(f'Initializing {tbl.__name__}')
        init_tbl = schema(tbl, context=context)
        context[tbl.__name__] = init_tbl
        init_tbls[tbl.__name__] = init_tbl

    return init_tbls


def init_ephys_pipeline(schema, subject, session, location):
    context = inspect.currentframe().f_back.f_locals

    # probe tables
    probe_tbls = _init_probe_tbls(schema, context)
    context.update(**probe_tbls)

    # configurable tables
    conf_tbls = _init_config_tbls(schema, subject, session, location, context)
    context.update(**conf_tbls)

    # non-configurable tables
    nonconf_tbls = _init_nonconfig_tbls(schema, context)

    return {**probe_tbls, **conf_tbls, **nonconf_tbls}
