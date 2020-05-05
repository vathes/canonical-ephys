from .ephys import *
from .probe import *


# ========================== REQUIREMENTS =========================
# Upstream tables and methods required to initialize the entire ephys pipeline

required_tbl_names = ('Subject', 'Session', 'Location')
required_method_names = ('get_npx_data_dir', 'get_ks_data_dir')


def check_requirements(requirements):
    if not requirements:
        emsg = u'"requirements" needs to be a dictionary with' \
               ' - Keys for upstream tables: {}' \
               ' - Keys for methods: {}'.format(required_tbl_names, required_method_names)
        raise KeyError(emsg)

    checked_requirements = {}
    for k in required_tbl_names:
        if k not in requirements:
            raise KeyError(f'Requiring upstream table: {k}')
        else:
            checked_requirements[k] = requirements[k]

    for k in required_method_names:
        if k not in requirements or not inspect.isfunction(requirements[k]):
            raise KeyError(f'Requiring method: {k}')
        else:
            checked_requirements[k] = requirements[k]

    return checked_requirements


# ========================== HELPER METHODS =======================

_probe_tbls = (ProbeType, Probe, ElectrodeConfig)

_config_tbls = (ProbeInsertion, InsertionLocation, EphysRecording)

_non_config_tbls = (LFP, ClusteringMethod, ClusterQualityLabel, Clustering, Unit, UnitSpikeTimes, Waveform)


def _init_probe_tbls(schema, context):
    init_tbls = {}
    for tbl in _probe_tbls:
        print(f'Initializing {tbl.__name__}')
        init_tbl = schema(tbl, context=context)
        context[tbl.__name__] = init_tbl
        init_tbls[tbl.__name__] = init_tbl

    return init_tbls


def _init_ephys_tbls(schema, requirements, context):
    init_tbls = {}
    for tbl in (_config_tbls + _non_config_tbls):
        for hook_name, hook_target in requirements.items():
            hook_name = f'_{hook_name}'
            if hook_name in dir(tbl):
                setattr(tbl, hook_name, hook_target)

        print(f'Initializing {tbl.__name__}')
        init_tbl = schema(tbl, context=context)
        context[tbl.__name__] = init_tbl
        init_tbls[tbl.__name__] = init_tbl

    return init_tbls


def init_ephys_pipeline(schema, requirements, context={}, add_here=False):
    requirements = check_requirements(requirements)

    if add_here and not context:
        context = inspect.currentframe().f_back.f_locals

    # probe tables
    probe_tbls = _init_probe_tbls(schema, context)
    context.update(**probe_tbls)

    # configurable tables
    ephys_tbls = _init_ephys_tbls(schema, requirements, context)

    ephys_pipeline = {**probe_tbls, **ephys_tbls}

    if add_here:
        context.update(**ephys_pipeline)

    return ephys_pipeline
