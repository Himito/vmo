"""
utils/nuxmv/properties.py
Variable Markov Oracle in python

@copyright: 
Copyright (C) 7.2015 Theis Bazin

This file is part of vmo.

@license: 
vmo is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

vmo is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with vmo.  If not, see <http://www.gnu.org/licenses/>.
@author: Cheng-i Wang, Theis Bazin
@contact: wangsix@gmail.com, chw160@ucsd.edu, tbazin@eng.ucsd.edu
"""

import numpy as np
from fractions import Fraction
import string
import copy

import music21 as music

import vmo.utils.nuxmv.model as model

"""nuXmv properties generation module."""

def pitch_equal(pitch, silence_equivalence=False, allow_init=False,
                nuxmv_pitch_name='pitchRoot',
                nuxmv_silence_name='p_Silence', nuxmv_empty_name='p_Init'):
    """Return a nuxmv string stating the current pitch root is `pitch`.
    
    Keyword arguments:
        pitch: string
            The name of the pitch to test equality with.
        silence_equivalence: bool, optional
            Whether silence should be considered equivalent to any given pitch
            (default False, since we then generate less interesting paths)
        allow_init: bool, optional
            Whether an empty state should be considered equivalent
            to any given pitch
            (default False, since we then generate less interesting paths)
        nuxmv_pitch_name: string, optional
            The name of the variable in the nuXmv model specifying
            the current pitch root (default 'pitchRoot')
        nuxmv_silence_name: string, optional
            The name of the nuxmv value specifying that the current
            state holds no notes (default 'p_Silence')
        nuxmv_empty_name: string, optional
            The name of the nuxmv value specifying that the current
            state is the initial state (default 'p_Init')
            (Note: could test for `state == 0`)
    """
    equality_test = "{0}={1}".format(nuxmv_pitch_name,
                                     pitch)
    if pitch != nuxmv_silence_name and silence_equivalence:
        equality_test = "{0} | {1}={2}".format(equality_test,
                                               nuxmv_pitch_name,
                                               nuxmv_silence_name)
    if allow_init:
        equality_test = "{0} | {1}={2}".format(equality_test,
                                               nuxmv_pitch_name,
                                               nuxmv_empty_name)
    return equality_test

def make_progression(progressions, exists=True,
                     silence_equivalence=False,
                     allow_init=False, nuxmv_pitch_name='pitchRoot',
                     nuxmv_silence_name='p_Silence',
                     nuxmv_motion_name='pitchMotion'):
    """Return a string stating the existence of a path following `progressions`.

    Keyword arguments:
        progressions: {(string, (int, int))} sequences
            The piecewise chord progression to test for, of the form:
            [PROG_1, PROG_2, ..., PROG_n].
            Each PROG_i should be continously satisfied.
            Arbitrary paths can be taken to connect each PROG_i though.
            
            Each PROG_i is a sequence of pairs of the form:
                The name of the root note, e.g. 'C#' or 'D-'
                The quarter-length duration for which the note should be held,
                as an interval `(minimum, maximum)` of acceptable durations.
                    `minimum` and `maximum` can be either `int`s or `None`.
            
        exists: bool
            The truth value to test
            (default True, should be False for counter-example generation). 
        silence_equivalence: bool, optional
            Whether silence should be considered equivalent to any given pitch
            (default False, since we then generate less interesting paths).
        allow_init: bool, optional
            Whether an empty state should be considered equivalent
            to any given pitch
            (default False, since we then generate less interesting paths).
        nuxmv_pitch_name: string
            The name of the nuxmv model variable representing the current pitch
            class.
        nuxmv_silence_name: string, optional
            The name of the nuxmv value specifying that the current
            state holds no notes (default 'p_Silence').
    """
    progressions_copy = copy.deepcopy(progressions)
    for progression in progressions_copy:
        # Necessary because list.pop() extracts `list`'s last element
        progression.reverse()
    
    def progressions_aux(progressions):
        if not progressions:
            # Empty progression, existence is trivial
            return 'TRUE'
        elif not progressions[0]:
            # The current progression is empty, existence of the sequence
            # depends only on the next progressions in `progressions`
            next_progressions = progressions_aux(progressions[1:])
            return "EF ({})".format(next_progressions)
        else:
            # Enforce next step in the current progression
            progression = progressions[0]
            motion = None
            
            next_elem = progression.pop()
            (pitch, (min_dur, max_dur)) = next_elem
            if pitch[0] == '+':
                motion = 'ascending'
                pitch = pitch[1:]
            elif pitch[0] == '-':
                motion = 'descending'
                pitch = pitch[1:]
            root_name = model.make_root_name(pitch)
            next_prop = progressions_aux(progressions)
            equality_test = pitch_equal(
                root_name,
                silence_equivalence=silence_equivalence,
                nuxmv_pitch_name=nuxmv_pitch_name,
                nuxmv_silence_name=nuxmv_silence_name)

            if min_dur == None:
                min_dur = 1
            if min_dur == None and max_dur == None:
                prop = "({0}) & E [({0}) U ({1})]".format(equality_test,
                                                          next_prop)
            
            # Enforce equality for at least `min_dur` steps
            interval_eq = "EBG {0} .. {1} ({2})".format(
                0, min_dur - 1, equality_test)
    
            if max_dur == None:
                # Enforce reachability of next interval
                # within at least `min_dur` steps
                reachability_prop = "E [({0}) BU {1} .. {1} (EF {2})]"
                reachability_prop = reachability_prop.format(
                    equality_test, min_dur, next_prop)
            else:    
                # Enforce reachability of next interval
                # between `min_dur` and `max_dur`
                reachability_prop = "E [({0}) BU {1} .. {2} ({3})]".format(
                    equality_test, min_dur, max_dur, next_prop)

            # Combine interval constraint and reachability
            prop = "({0}) & ({1})".format(interval_eq, reachability_prop)
            
            if motion:
                prop = "({0}={1}) & {2}".format(nuxmv_motion_name,
                                                'm_asc' if motion=='ascending'
                                                else 'm_desc',
                                                prop)
                                         
            
            return prop
    
    return "CTLSPEC {1}(EF ({0}))".format(progressions_aux(progressions_copy),
                                     # Account for possible negation
                                     '' if exists else '!')
