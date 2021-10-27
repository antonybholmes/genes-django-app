#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan  9 13:59:50 2020

@author: antony
"""

from rest_framework import serializers

class SourceSerializer(serializers.Serializer):
    genome = serializers.CharField(max_length=255)
    assembly = serializers.CharField(max_length=255)
    track = serializers.CharField(max_length=255)