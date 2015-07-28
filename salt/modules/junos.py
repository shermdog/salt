# -*- coding: utf-8 -*-
'''
Module for interfacing to Junos devices

ALPHA QUALITY code.

'''
from __future__ import absolute_import

# Import python libraries
import logging
import re
import json

# Juniper interface libraries
# https://github.com/Juniper/py-junos-eznc
try:
    # pylint: disable=W0611
    import jnpr.junos
    import jnpr.junos.utils
    import jnpr.junos.cfg
    from jnpr.junos.utils.sw import SW
    from jnpr.junos.exception import LockError, UnlockError, ConfigLoadError
    from jnpr.junos.version import VERSION
    # pylint: enable=W0611
    if not float(re.match('\d+.\d+', VERSION).group()) >= 1.2:
        HAS_PYEZ = False
    else:
        HAS_PYEZ = True
except ImportError:
    HAS_PYEZ = False


# Set up logging
log = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'junos'

__proxyenabled__ = ['junos']


def __virtual__():
    '''
    We need the Junos adapter libraries for this
    module to work.  We also need a proxymodule entry in __opts__
    in the opts dictionary
    '''
    if HAS_PYEZ and 'proxymodule' in __opts__:
        return __virtualname__
    else:
        return False


def facts_refresh():
    '''
    Reload the facts dictionary from the device.  Usually only needed
    if the device configuration is changed by some other actor.
    '''

    return __opts__['proxymodule']['junos.conn']().refresh()


def lock():
    conn = __opts__['proxymodule']['junos.conn']()
    ret = dict()

    log.debug('taking lock')
    try:
        conn.cu.lock()
        log.debug('locked config')
        ret['out'] = True
        ret['msg'] = 'locked config'
    except LockError:
        log.debug('could not lock config!')
        ret['out'] = False
        ret['msg'] = 'could not lock config!'

    return ret


def rpc(rpc_cmd, **kwargs):
    conn = __opts__['proxymodule']['junos.conn']()
    try:
        return json.dumps(conn.rpc.__getattr__(rpc_cmd)(**kwargs))
    except Exception as e:
        ret = dict()
        ret['msg'] = e
        ret['out'] = False
        return ret


def unlock():
    conn = __opts__['proxymodule']['junos.conn']()
    ret = dict()

    log.debug('unlocking config')
    try:
        conn.cu.unlock()
        log.debug('unlocked config')
        ret['out'] = True
        ret['msg'] = 'unlocked config'
    except UnlockError:
        log.debug('could not unlock config!')
        ret['out'] = False
        ret['msg'] = 'could not unlock config!'

    return ret


def load_config(*vargs, **kwargs):
    conn = __opts__['proxymodule']['junos.conn']()
    ret = dict()

    lock()

    try:
        log.debug('Loading Configuration')
        conn.cu.load(*vargs, **kwargs)
        commit()
        ret['out'] = True
        ret['msg'] = 'Successfully loaded configuration'
    except Exception as e:
        ret['out'] = False
        error_msg = 'Failed to load config: {0}'.format(e)
        log.error(error_msg)
        ret['msg'] = error_msg
        unlock()

    unlock()

    return ret


def commit_check():
    conn = __opts__['proxymodule']['junos.conn']()
    return conn.cu.commit_check()


def commit():

    conn = __opts__['proxymodule']['junos.conn']()

    ret = {}
    commit_ok = commit_check()
    if commit_ok:
        try:
            conn.cu.commit()
            ret['out'] = True
            ret['message'] = 'Commit Successful.'
        except Exception as e:
            ret['out'] = False
            ret['message'] = 'Pre-commit check succeeded but actual commit failed with "{0}"'.format(e.message)
    else:
        ret['out'] = False
        ret['message'] = 'Pre-commit check failed.'

    return ret


def shutdown(reboot=False, in_min=0, at=None):
    conn = __opts__['proxymodule']['junos.conn']()
    ret = {}

    sw = SW(conn)
    if reboot is True:
        ret['message'] = 'Reboot in: {0}, at: {1}'.format(in_min, at)
        sw.reboot(in_min, at)
    else:
        ret['message'] = 'Shutdown in: {0}'.format(in_min)
        sw.poweroff(in_min)
    ret['out'] = True
    return ret


def rollback(rb_id=0):
    conn = __opts__['proxymodule']['junos.conn']()
    ret = dict()

    ret['out'] = conn.cu.rollback(rb_id=rb_id)

    if ret['out']:
        ret['message'] = 'Rollback successful'
    else:
        ret['message'] = 'Rollback failed'

    return ret


def diff():

    ret = dict()
    conn = __opts__['proxymodule']['junos.conn']()
    ret['out'] = True
    ret['message'] = conn.cu.diff()

    return ret


def ping():
    conn = __opts__['proxymodule']['junos.conn']()
    return conn.probe()
