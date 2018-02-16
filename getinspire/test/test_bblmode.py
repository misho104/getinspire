#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import tempfile
import os.path
import shutil
import subprocess
import sys
import re
from compiler.ast import flatten

TEST_DATA   = os.path.join(os.path.dirname(__file__), "data")
TEST_SCRIPT = ["python", os.path.join(os.path.realpath(os.path.dirname(__file__)), "..", "..", "getinspire")]

BIBKEY_MAP = {
    'astro-ph/0302209': {'key': 'Spergel:2003cb',   'title':'First year Wilkinson Microwave'},
    '0803.0547':        {'key': 'Komatsu:2008hk',   'title':'Five-Year Wilkinson Microwave'},
    'hep-th/9908142':   {'key': 'Seiberg:1999vs',   'title':''},
    'hep-th/9905111':   {'key': 'Aharony:1999ti',   'title':''},
    'Maldacena:1997re': {'key': 'Maldacena:1997re', 'title':'The Large N limit of'},
    'Salpeter:1955it':  {'key': 'Salpeter:1955it',  'title':''},
}


try:
    from subprocess import DEVNULL # py3k
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')

class TestGetInspireBBL(unittest.TestCase):
    texfile = "bbl.tex"

    @classmethod
    def setUpClass(cls):
        cls.temp_dir     = tempfile.mkdtemp()
        cls.test_dir     = os.path.join(cls.temp_dir, "data")
        cls.texfile_path = os.path.join(cls.test_dir, cls.texfile)

        shutil.copytree(TEST_DATA, cls.test_dir)
        print "Tests are run in a temporary directory " + cls.test_dir + "."

        cmd = " ".join(flatten([TEST_SCRIPT, "-t", cls.texfile]))
        subprocess.check_call(cmd, shell=True, cwd = cls.test_dir, stderr=subprocess.STDOUT)

        cls.src = {}
        with open(os.path.join(TEST_DATA, cls.texfile)) as f:
            cls.src['tex'] = f.read()

        cls.out = {}
        with open(cls.texfile_path) as f:
            cls.out['tex'] = f.read()
        with open(re.sub(r'\.tex$', '.bbl', cls.texfile_path)) as f:
            cls.out['bbl'] = f.read()

#    def test_validity_of_output(self):
#        cmd = " ".join(["pdflatex", "-halt-on-error", cls.texfile])
#        retval = subprocess.call(cmd, shell=True, cwd = cls.test_dir)
#        cls.assertEqual(retval, 0)
#        cls.assertTrue(os.path.exists(re.sub(r'\.tex$', '.pdf', cls.texfile_path)))

    def cite_keys(self, tex):
        cites = re.findall(r'\\cite\{(.*?)\}', tex, re.DOTALL)
        cites = flatten(map(lambda key: key.split(","), cites))
        cites = map(lambda key: key.strip(), cites)
        return cites

    def test_bbl_file_validity(self, output=None):
        if output is None:
            output = self.out
        self.assertTrue(re.search(r"\\begin\{thebibliography\}\{\d+\}.*\\end\{thebibliography\}", output['bbl'], re.DOTALL))

    def test_bbl_file_has_all_cites(self, output=None):
        if output is None:
            output = self.out
        in_keys = self.cite_keys(self.src['tex'])
        bbl_keys = re.findall(r'\\bibitem{(.*?)}', output['bbl'], re.DOTALL)
        self.assertEqual(map(lambda k: BIBKEY_MAP[k]['key'], in_keys), bbl_keys)

    def test_bibkey_in_tex_are_replaced(self, output=None):
        if output is None:
            output = self.out
        in_keys = self.cite_keys(self.src['tex'])
        out_keys = self.cite_keys(output['tex'])
        self.assertEqual(map(lambda k: BIBKEY_MAP[k]['key'], in_keys), out_keys)

    def test_bbl_file_has_correct_information(self, output=None):
        if output is None:
            output = self.out

        bbl_items = map(lambda s: "\\bibitem" + s, output['bbl'].split("\\bibitem")[1:])

        for item in bbl_items:
            key = re.findall(r'\\bibitem{(.*?)}', item, re.DOTALL)[0]
            substr_of_title = [ v['title'] for k, v in BIBKEY_MAP.iteritems() if v['key'] == key ][0]
            self.assertTrue(substr_of_title in item)

    def test_zzz_rerun_append_do_nothing(self):
        cmd = " ".join(flatten([TEST_SCRIPT, "-a", self.texfile]))
        subprocess.check_call(cmd, shell=True, cwd = self.test_dir, stdout=DEVNULL, stderr=DEVNULL)

        output = {}
        with open(self.texfile_path) as f:
            output['tex'] = f.read()
        with open(re.sub(r'\.tex$', '.bbl', self.texfile_path)) as f:
            output['bbl'] = f.read()

        self.test_bbl_file_validity(output=output)
        self.test_bbl_file_has_all_cites(output=output)
        self.test_bibkey_in_tex_are_replaced(output=output)
        self.test_bbl_file_has_correct_information(output=output)

if __name__ == '__main__':
    unittest.main()
