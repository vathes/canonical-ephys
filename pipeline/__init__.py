import inspect
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


# ========================== SINGLETON TABLE-SET =======================

class OneEphysPipeline:
    __instance = None

    def __init__(self):
        if OneEphysPipeline.__instance is None:
            OneEphysPipeline.__instance = True
        else:
            raise RuntimeError('Unable to initialize ephys pipeline twice!')

    def exists(self):
        return bool(self.__instance)

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

    # Insert probe details
    probe_types = ('neuropixels 1.0 - 3A', 'neuropixels 1.0 - 3B',
                   'neuropixels 2.0 - SS', 'neuropixels 2.0 - MS')
    for probe_type in probe_types:
        if {'probe_type': probe_type} not in ProbeType.proj():
            ProbeType().create_neuropixels_probe(probe_type)

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
    if OneEphysPipeline().exists():
        raise RuntimeError('Unable to initialize ephys pipeline twice!')

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

    OneEphysPipeline()

    return ephys_pipeline
