import sys

def search_magnitude(meta_data_array):
    """ Return indices of magnitude images from an array of meta-data.
    """
    
    indices = []
    for index, meta_data in enumerate(meta_data_array):
        if meta_data.get("Manufacturer", [None])[0] == "SIEMENS":
            if meta_data.get("ImageType", [None, None, None])[2] == "M":
                indices.append(index)
    return indices

def search_phase(meta_data_array):
    """ Return indices of phase images from an array of meta-data.
    """
    
    indices = []
    for index, meta_data in enumerate(meta_data_array):
        if meta_data.get("Manufacturer", [None])[0] == "SIEMENS":
            if meta_data.get("ImageType", [None, None, None])[2] == "P":
                indices.append(index)
    return indices
