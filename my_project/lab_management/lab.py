import datajoint as dj

schema = dj.schema('u24_lab_')


@schema
class Subject(dj.Manual):
    definition = """
    subject_id: varchar(64)
    ---
    sex: enum('F', 'M', 'U')
    dob: datetime
    """


@schema
class Session(dj.Manual):
    definition = """
    -> Subject
    session_datetime: datetime
    """


@schema
class SkullReference(dj.Lookup):
    definition = """
    skull_reference   : varchar(60)
    """
    contents = zip(['Bregma', 'Lambda'])


@schema
class LocationDataSource(dj.Lookup):
    definition = """
    location_data_source: varchar(36)    
    """


@schema
class Location(dj.Manual):
    definition = """
    location_id: uuid
    ---
    -> LocationDataSource
    -> SkullReference
    ap_location: decimal(6, 2) # (um) anterior-posterior; ref is 0; more anterior is more positive
    ml_location: decimal(6, 2) # (um) medial axis; ref is 0 ; more right is more positive
    depth:       decimal(6, 2) # (um) manipulator depth relative to surface of the brain (0); more ventral is more negative
    theta:       decimal(5, 2) # (deg) - elevation - rotation about the ml-axis [0, 180] - w.r.t the z+ axis
    phi:         decimal(5, 2) # (deg) - azimuth - rotation about the dv-axis [0, 360] - w.r.t the x+ axis
    beta:        decimal(5, 2) # (deg) rotation about the shank of the probe [-180, 180] - clockwise is increasing in degree - 0 is the probe-front facing anterior
    """
