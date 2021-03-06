"""Utilities for preparing VASP - INCAR files"""
import numpy as np


def _incarify(value):
    """Format value of any compatible type into the string forat appropriate for INCAR files"""
    result = None
    if isinstance(value, (str, unicode)):
        result = value
    elif not np.isscalar(value):
        value_array = np.array(value)
        shape = value_array.shape
        dim = len(shape)
        if dim == 1:
            result = ' '.join([_incarify(i) for i in value])
        elif dim == 2:
            result = '\n'.join([_incarify(i) for i in value])
        elif dim > 2:
            raise TypeError('you are trying to input a more ' +
                            'than 2-dimensional array to VASP.' +
                            'Not sure what to do...')
    elif isinstance(value, bool):
        result = '.True.' if value else '.False.'
    elif np.isreal(value):
        result = '{}'.format(value)
    return result


def _incar_item(key, value):
    return _incar_item.tpl.format(key=key.upper(), value=_incarify(value))


_incar_item.tpl = '{key} = {value}'


def dict_to_incar(incar_dict):
    incar_content = ''
    for key, value in sorted(incar_dict.iteritems(), key=lambda t: t):
        incar_content += _incar_item(key, value) + '\n'
    return incar_content
