import os
import logging
import configparser
import tempfile

from seafevents.utils import has_office_tools, has_offline_download_tools


def parse_workers(workers, default_workers):
    try:
        workers = int(workers)
    except ValueError:
        logging.warning('invalid workers value "%s"' % workers)
        workers = default_workers

    if workers <= 0 or workers > 5:
        logging.warning('insane workers value "%s"' % workers)
        workers = default_workers

    return workers

def parse_max_size(val, default):
    try:
        val = int(val.lower().rstrip('mb')) * 1024 * 1024
    except:
        logging.exception('xxx:')
        val = default

    return val

def parse_max_pages(val, default):
    try:
        val = int(val)
        if val <= 0:
            val = default
    except:
        val = default

    return val

def get_opt_from_conf_or_env(config, section, key, env_key=None, default=None):
    '''Get option value from events.conf. If not specified in events.conf,
    check the environment variable.

    '''
    try:
        return config.get(section, key)
    except configparser.NoOptionError:
        if env_key is None:
            return default
        else:
            return os.environ.get(env_key.upper(), default)

def parse_bool(v):
    if isinstance(v, bool):
        return v

    v = str(v).lower()

    if v == '1' or v == 'true':
        return True
    else:
        return False

def parse_interval(interval, default):
    if isinstance(interval, (int, int)):
        return interval

    interval = interval.lower()

    unit = 1
    if interval.endswith('s'):
        pass
    elif interval.endswith('m'):
        unit *= 60
    elif interval.endswith('h'):
        unit *= 60 * 60
    elif interval.endswith('d'):
        unit *= 60 * 60 * 24
    else:
        pass

    val = int(interval.rstrip('smhd')) * unit
    if val < 10:
        logging.warning('insane interval %s', val)
        return default
    else:
        return val


def get_offline_download_conf(config):
    '''Parse offline download options from seafevents.conf'''
    if not has_offline_download_tools():
        logging.debug('offline downloader is not enabled because Aria2 is not found')
        return dict(enabled=False)

    section_name = 'OFFLINE DOWNLOAD'
    key_enabled = 'enabled'

    key_tempdir = 'tempdir'
    default_tempdir = os.path.join(tempfile.gettempdir(), 'seafile-office-output')

    key_workers = 'workers'
    default_workers = 10

    key_time_limit = 'time-limit'
    default_time_limit = 30 * 60      # in seconds, default is 30 minutes

    d = {'enabled': False}
    if not config.has_section(section_name):
        return d

    def get_option(key, default=None):
        try:
            value = config.get(section_name, key)
        except configparser.NoOptionError:
            value = default

        return value

    enabled = get_option(key_enabled, default=False)
    enabled = parse_bool(enabled)
    d['enabled'] = enabled
    logging.debug('offline download enabled: %s', enabled)
    if not enabled:
        return d

    # [ outputdir ]
    tempdir = get_option(key_tempdir, default=default_tempdir)

    if not os.path.exists(tempdir):
        try:
            os.mkdir(tempdir)
        except Exception as e:
            logging.error(e)

    if not os.access(tempdir, os.R_OK):
        logging.error('Permission Denied: %s is not readable' % tempdir)

    if not os.access(tempdir, os.W_OK):
        logging.error('Permission Denied: %s is not allowed to be written.' % tempdir)

    # [ workers ]
    workers = get_option(key_workers, default=default_workers)
    workers = parse_workers(workers, default_workers)

    # [ max_size ]
    time_limit = get_option(key_time_limit, default=default_time_limit)
    if time_limit != default_time_limit:
        time_limit = parse_interval(time_limit, default=default_time_limit)

    logging.debug('offline download tempdir: %s', tempdir)
    logging.debug('offline download workers: %s', workers)
    logging.debug('offline download time limit: %s seconds', time_limit)

    d['tempdir'] = tempdir
    d['workers'] = workers
    d['time-limit'] = time_limit
    return d


def get_office_converter_conf(config):
    '''Parse search related options from seafevents.conf'''

    if not has_office_tools():
        logging.debug('office converter is not enabled because libreoffice or python-uno is not found')
        return dict(enabled=False)

    section_name = 'OFFICE CONVERTER'
    key_enabled = 'enabled'

    key_outputdir = 'outputdir'
    default_outputdir = os.path.join(tempfile.gettempdir(), 'seafile-office-output')

    key_workers = 'workers'
    default_workers = 2

    key_max_pages = 'max-pages'
    default_max_pages = 50

    key_max_size = 'time-limit'
    default_max_size = 30 * 60      # 30 minutes

    key_host = 'host'
    default_host = '127.0.0.1'

    key_port = 'port'
    default_port = 6000

    d = {'enabled': False}
    if not config.has_section(section_name):
        return d

    def get_option(key, default=None):
        try:
            value = config.get(section_name, key)
        except configparser.NoOptionError:
            value = default

        return value

    enabled = get_option(key_enabled, default=False)
    enabled = parse_bool(enabled)

    d['enabled'] = enabled
    logging.debug('office enabled: %s', enabled)

    if not enabled:
        return d

    # [ outputdir ]
    outputdir = get_option(key_outputdir, default=default_outputdir)

    if not os.path.exists(outputdir):
        try:
            os.mkdir(outputdir)
        except Exception as e:
            logging.error(e)

    if not os.access(outputdir, os.R_OK):
        logging.error('Permission Denied: %s is not readable' % outputdir)

    if not os.access(outputdir, os.W_OK):
        logging.error('Permission Denied: %s is not allowed to be written.' % outputdir)

    # [ workers ]
    workers = get_option(key_workers, default=default_workers)
    workers = parse_workers(workers, default_workers)


    # [ max_size ]
    max_size = get_option(key_max_size, default=default_max_size)
    if max_size != default_max_size:
        max_size = parse_max_size(max_size, default=default_max_size)

    # [ max_pages ]
    max_pages = get_option(key_max_pages, default=default_max_pages)
    if max_pages != default_max_pages:
        max_pages = parse_max_pages(max_pages, default=default_max_pages)

    # [ http server address ]
    host = get_option(key_host, default=default_host)
    port = get_option(key_port, default=default_port)

    logging.debug('office convert workers: %s', workers)
    logging.debug('office outputdir: %s', outputdir)
    logging.debug('office convert max pages: %s', max_pages)
    logging.debug('office convert max size: %s MB', max_size / 1024 / 1024)
    logging.debug('office http server host: %s', host)
    logging.debug('office http server port: %s', port)

    d['outputdir'] = outputdir
    d['workers'] = workers
    d['max_pages'] = max_pages
    d['max_size'] = max_size
    d['host'] = host
    d['port'] = port

    return d
