# coding: UTF-8

import os
import tempfile
import subprocess
import logging
import re
import chardet
from zipfile import ZipFile
from io import BytesIO

from .utils import run
from .constants import text_suffixes, office_suffixes, ZERO_OBJ_ID
from .config import seafes_config

from seafobj import fs_mgr

logger = logging.getLogger('seafes')

class ZipString(ZipFile):
    def __init__(self, content):
        ZipFile.__init__(self, BytesIO(content))

def extract_html_text(content):
    return re.sub('<(.|\n)*?>', ' ', content)

def extract_poi_text(content):
    cwd = os.path.dirname(os.path.abspath(__file__))
    jarfile = os.path.join(cwd, 'poi/ExtractText.jar')
    cmd = ['timeout', str(seafes_config.content_extract_time * 60), 'java', '-Dfile.encoding=UTF-8', '-jar', jarfile]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    p.stdin.write(content)
    p.stdin.close()
    content = b''
    while True:
        data = p.stdout.read()
        if not data:
            break

        content += data

    p.wait()

    return content

def extract_pdf_text(content):
    temp_pdf = tempfile.NamedTemporaryFile()
    temp_txt = tempfile.NamedTemporaryFile()
    try:
        pdf_name = temp_pdf.name
        txt_name = temp_txt.name
        with open(pdf_name, 'wb') as output:
            output.write(content)

        cmd = ['timeout', str(seafes_config.content_extract_time * 60), 'pdftotext', pdf_name, txt_name]
        if run(cmd) != 0:
            content = None
        else:
            with open(txt_name, 'rb') as fp:
                content = fp.read()

        return content
    except Exception as e:
        logger.error('error when extracting pdf: %s', e)
        return None
    finally:
        temp_pdf.close()
        temp_txt.close()

def extract_docx_text(content):
    doc = ZipString(content)
    content = doc.read('word/document.xml')
    cleaned = re.sub('<(.|\n)*?>', ' ', content.decode())
    return cleaned.encode()

def extract_pptx_text(content):
    doc = ZipString(content)
    unpacked = doc.infolist()
    slides = []
    for item in unpacked:
        if item.orig_filename.startswith('ppt/slides') or item.orig_filename.startswith('ppt/notesSlides'):
            if item.orig_filename.endswith('xml'):
                slides.append(doc.read(item.orig_filename).decode())

    content = ''.join(slides)
    cleaned = re.sub('<(.|\n)*?>', ' ', content)
    return cleaned.encode()

def extract_xlsx_text(content):
    doc = ZipString(content)
    unpacked = doc.infolist()
    slides = []
    for item in unpacked:
        if item.orig_filename.startswith('xl/worksheets') or item.orig_filename.startswith('xl/sharedStrings.xml'):
            if item.orig_filename.endswith('xml'):
                slides.append(doc.read(item.orig_filename).decode())

    content = ''.join(slides)
    cleaned = re.sub('<(.|\n)*?>', ' ', content)
    return cleaned.encode()


def extract_odf_text(content):
    doc = ZipString(content)
    content = doc.read('content.xml')
    cleaned = re.sub('<(.|\n)*?>', ' ', content.decode())
    return cleaned.encode()


EXTRACT_TEXT_FUNCS = {
    'htm': extract_html_text,
    'html': extract_html_text,
    'xhtml': extract_html_text,
    'docx': extract_docx_text,
    'pptx': extract_pptx_text,
    'xlsx': extract_xlsx_text,
    'doc': extract_poi_text,
    'xls': extract_poi_text,
    'ppt': extract_poi_text,
    'pdf': extract_pdf_text,
    'odt': extract_odf_text,
    'ods': extract_odf_text,
    'odp': extract_odf_text,
}

EXTRACT_TEXT_FUNCS.update(dict([(suffix, lambda content, *args: content)
                                for suffix in text_suffixes]))

def get_file_suffix(path):
    try:
        name = os.path.basename(path)
        suffix = os.path.splitext(name)[1][1:]
        if suffix:
            return suffix.lower()
        return None
    except:
        return None


def is_text_file(path):
    suffix = get_file_suffix(path)
    if not suffix:
        return False

    if suffix in text_suffixes:
        return True

    return False

def is_office_pdf(path):
    suffix = get_file_suffix(path)
    if not suffix:
        return False

    if suffix in office_suffixes:
        return True

    return False

def is_text_office(filename):
    return is_text_file(filename) or is_office_pdf(filename)

class Extractor(object):
    def __init__(self, func, file_size_limit):
        self.func = func
        self.file_size_limit = file_size_limit

    def extract(self, repo_id, version, obj_id, path):
        if obj_id == ZERO_OBJ_ID:
            return None

        f = fs_mgr.load_seafile(repo_id, version, obj_id)
        if self.file_size_limit < f.size:
            logger.warning("file %s size exceeds limit", path)
            return None
        content = f.get_content(limit=self.file_size_limit)
        if not content:
            # An empty file
            return None
        try:
            logger.info('extracting %s %s...', repo_id, path)
            content = self.func(content)
            logger.info('successfully extracted %s', path)
        except Exception as e:
            logger.error('failed to extract %s: %s', path, e)
            return None

        return self.fix_encoding(repo_id, path, content)

    def fix_encoding(self, repo_id, path, content):
        if not content:
            return None
        enc = chardet.detect(content[:4000]).get('encoding', None)
        if not enc:
            logger.warning('%s %s: encoding is unknown', repo_id, path)
            return None
        enc = enc.lower()

        try:
            content = content.decode(enc).encode('utf-8').decode('utf-8')
        except Exception as e:
            logger.error('%s: %s failed to trans code from %s to utf-8, because: %s', repo_id, path, enc, e)
            return None

        return content


class ExtractorFactory(object):
    @classmethod
    def get_extractor(cls, filename):
        if not cls.should_extract(filename):
            return None

        suffix = get_file_suffix(filename)
        func = EXTRACT_TEXT_FUNCS.get(suffix, None)
        if not func:
            return None
        return Extractor(func, cls.get_file_size_limit(filename))

    @classmethod
    def should_extract(cls, filename):
        return seafes_config.index_office_pdf and is_text_office(filename)

    @classmethod
    def get_file_size_limit(cls, filename):
        if is_text_file(filename):
            limit = seafes_config.text_size_limit
        elif is_office_pdf(filename):
            limit = seafes_config.office_file_size_limit
        else:
            limit = -1
        return limit
