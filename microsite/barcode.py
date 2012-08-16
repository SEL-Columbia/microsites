
import os
import tempfile
import StringIO
import base64
import uuid

from elaphe import barcode


def generate_qrcodefile(message, filename=None):

    if not filename:
        fileh, filename = tempfile.mkstemp(suffix='.png')
        os.close(fileh)

    code = generate_qrcode(message, stream=filename)

    return code


def generate_qrcode(message, stream=StringIO.StringIO(),
                    eclevel='M', margin=10,
                    data_mode='8bits', format='PNG'):

    img = barcode('qrcode', message, 
                  options=dict(version=9, eclevel=eclevel), 
                  margin=margin, data_mode=data_mode)

    if isinstance(stream, basestring):
        for ext in ('jpg', 'png', 'gif', 'bmp', 'xcf', 'pdf'):
            if stream.lower().endswith('.%s' % ext):
                img.save(stream)
                return stream

    img.save(stream, format)

    return stream


def b64_random_qrcode(as_tuple=False):
    ''' base64 encoded PNG image representing a QRCode of a random ID '''

    qr_id = get_random_id()
    qr_short_id = short_id_from(qr_id)
    b64_data = base64.b64encode(generate_qrcode(qr_id).getvalue())

    if as_tuple:
        return (qr_id, b64_data, qr_short_id)

    return b64_data


def get_random_id():
    return uuid.uuid4().hex


def dec2hex(n):
    ''' return the hexadecimal string representation of integer n '''
    return "%X" % n

def hex2dec(s):
    ''' return the integer value of a hexadecimal string s '''
    return int(s, 16)


def short_id_from(qr_id):
    ''' short ID is hex form of 10 million modulo on uuid. ~6 chars long'''
    return dec2hex(hex2dec(qr_id) % 10000000)