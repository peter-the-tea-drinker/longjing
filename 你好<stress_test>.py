#!/usr/bin/env python
# -*- coding: utf-8 -*-


def test_func():
    s = ''
    for i in range(100):
        s+='丁丁丁'
        
from example_app import statserver
statserver.profile(test_func)
