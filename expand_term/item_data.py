from cona_ia_list import get_cona_ia_list
from loc_list import get_loc_list
from term_list import get_term_list


def get_item_data(uri):
    if("http://www.getty.edu/cona/" in uri):
        getresponse = get_cona_ia_list(uri)
    elif("http://www.loc.gov/item/" in uri):
        getresponse = get_loc_list(uri)
    elif("vocab.getty.edu/" in uri):
        getresponse = get_term_list(uri)
    else:
        getresponse = "Unable to parse URI"
    return getresponse
