import datajoint as dj

from lab_management import lab

from pipeline import init_ephys_pipeline

schema = dj.schema('u24_ephys_')

ephys_tbls = init_ephys_pipeline(schema, lab.Subject, lab.Session, lab.Location)

locals().update(**ephys_tbls)

