
import random

CHARS = "abcdefghijklmnopqrstuvwxyz12345679ABCDEFGHIJKLMNOPQRSTUVWXYZ"
SPID_LEN = 6


def generate_spid(country_code='US'):  
    ''' Generate a SPID_LEN random string prefix with XX- with XX as country '''
    return '%s-%s' % (country_code.upper(), ''.join([random.choice(CHARS)
           for i in range(1, SPID_LEN + 1)]))


def ssids_from_spid(spid):
    ''' List of 6 strings containing spid suffixed with 1-6 '''
    return ['%s-%d' % (spid, index) for index in range(1, 7)]


def generate_ssids(country_code):
    ''' Generate a list of 6 SSIDs from a country code '''
    return ssids_from_spid(generate_spid(country_code))