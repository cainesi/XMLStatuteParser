#$Id :$

"""Module for provides functions for processing statute language (e.g., the applicability provisions of statutes, definitions, cross-references)."""

import re

class textParse(object):
    def __init__(self, text):
        self.text = text
