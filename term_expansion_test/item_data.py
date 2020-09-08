from cona_ia_list import get_cona_ia_list
from loc_list import get_loc_list
from term_list import get_term_list


def get_item_data(subject):
    if(subject.get("authority").lower() == "ia"):
        getresponse = get_cona_ia_list(subject['uri'])
    elif(subject.get("authority").lower() == "loc"):
        getresponse = get_loc_list(subject['term'])
    elif(subject.get("authority").lower() == "aat"):
        getresponse = get_term_list(subject['uri'])
    else:
        getresponse = []

    return getresponse
