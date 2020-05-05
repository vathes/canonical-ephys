import datajoint as dj

from my_project.utils import get_ephys_probe_data_dir, get_ks_data_dir

from my_project.lab_management import lab

# ---------

from pipeline import init_ephys_pipeline

schema = dj.schema('u24_ephys_')

requirements = {'Subject': lab.Subject,
                'Session': lab.Session,
                'Location': lab.Location,
                'get_npx_data_dir': get_ephys_probe_data_dir,
                'get_ks_data_dir': get_ks_data_dir}

ephys_tbls = init_ephys_pipeline(schema, requirements, add_here=False)
