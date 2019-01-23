#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan  3 12:08:30 2019

@author: omarschall
"""

import numpy as np

def norm(z):
    
   return np.sqrt(np.sum(np.square(z)))

def split_weight_matrix(A, sizes, axis=1):
    
    indices = [0] + np.cumsum(sizes).tolist()
    return [A[:,indices[i]:indices[i+1]] for i in range(len(indices) - 1)]