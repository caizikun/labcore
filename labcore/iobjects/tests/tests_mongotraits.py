# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 17:26:40 2014

@author: zah
"""
import unittest

import mongoengine as mg
from mongoengine.connection import _get_db
import mongoengine.fields as fields
from IPython.utils import traitlets

from labcore.iobjects.mongotraits import (Document,
    EmbeddedDocument, EmbeddedReferenceField)

from labcore.iobjects.tests.common import Doc, EmbDoc,Partner
from labcore.iobjects.tests.base import MongoTest

class Test_base(MongoTest):
    def test_bassic(self):
        refs = [EmbDoc(name = i) for i in "xyzt"]
        t = Doc()
        t.refs = refs
        assert(refs[0].id is not None)
        x = Partner(name = "p")
        x.ref = refs[3]
        t.partner = x
        assert(t.partner.ref is refs[3])
        t.save()
        self.assertTrue(Doc.objects.all()[0] is t)
        del(t)
        t2 = Doc.objects.all()[0]
        self.assertTrue(t2.partner.ref is refs[3])
    def test_traits(self):
        doc = Doc()
        
        def ns(): pass
        ns.x = None       
        def fchanged():
            print ("sdasdas")
            ns.x = 'OK'
        doc.on_trait_change(fchanged ,name = 'f')
        self.assertIsNone(ns.x)
        doc.f = True
        self.assertEqual(ns.x, 'OK')

if __name__ == '__main__':
    unittest.main()