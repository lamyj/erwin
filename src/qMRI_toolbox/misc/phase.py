import logging
import numpy

def get_phase_data(data, meta_data):
    """ Return the phase data, in rad, from a raw phase image.
    """
    
    if meta_data.get("Manufacturer", [None])[0] == "SIEMENS":
        return data/4096*numpy.pi
    else:
        logging.warning("Unknown manufacturer, return data as-is")
        return data
