#! /usr/bin/env python

##
# @file  doxygen-bash-filter.py
# @brief Doxygen filter for BASH scripts.
#
# Copyright (c) 2011 University of Pennsylvania. All rights reserved.
# See https://www.rad.upenn.edu/sbia/software/license.html or COPYING file.
#
# Contact: SBIA Group <sbia-software at uphs.upenn.edu>
#
# @ingroup CMakeHelpers

import sys
import re

if __name__ == "__main__":
    # parse arguments
    if len (sys.argv) != 2:
        sys.stderr.write ("No file specified to process!\n")
        sys.exit (1)
    fileName = sys.argv [1]
    # open input file
    f = open (fileName, 'r')
    if not f:
        sys.stderr.write ("Failed to open file " + fileName + " for reading!\n")
        sys.exit (1)
    # compile regular expressions
    reShaBang       = re.compile (r"#!\s*/usr/bin/env\s+bash$|#!\s*/bin/bash$")
    reInclude       = re.compile (r"source\s+[\"']?(?P<module>.+)[\"']?$")
    reFunctionStart = re.compile (r"function\s*(?P<name>\w+)\s*{?")
    reFunctionEnd   = re.compile (r"}$")
    reCommentStart  = re.compile (r"##+(?P<comment>.*)$")
    reCommentLine   = re.compile (r"#+(?P<comment>.*)$")
    reParamDoc      = re.compile (r"[\@\\]param\s+(\[\s*(in|out|in\s*,\s*out|out\s*,\s*in)\s*\]|\s*)\s+(?P<param>\w+)")
    reIfClauseStart = re.compile (r"if\s*\[")
    reIfClauseEnd   = re.compile (r"else[\s$]|elif\s*\[|;?fi$")

    # parse line-by-line and output pseudo C++ code to stdout
    ifClauseDepth = 0     # current depth of if-clauses
    commentDepth  = 0     # if-clause depth where comment was encountered
    previousBlock = ''    # name of previous code block
    currentBlock  = ''    # name of current code block
    params        = []
    for line in f:
        line = line.strip ()
        # skip sha-bang directive
        if reShaBang.match (line) is not None:
            sys.stdout.write ("\n")
            continue
        # next comment line,
        if currentBlock == 'comment':
            m = reCommentLine.match (line)
            if m is not None:
                comment = m.group ('comment')
                sys.stdout.write ("///" + comment + "\n")
                m = reParamDoc.search (line)
                if m is not None:
                    param = m.group ('param')
                    params.append (param)
                continue
            else:
                previousBlock = currentBlock
                currentBlock = ''
                # continue processing of this (yet unhandled) line
        # inside function definition
        if currentBlock == 'function':
            m = reFunctionEnd.match (line)
            if m is not None:
                previousBlock = currentBlock
                currentBlock = ''
            sys.stdout.write ("\n")
            continue
        # look for new comment block or block following a comment
        if currentBlock == '':
            # include
            m = reInclude.match (line)
            if m is not None:
                module = m.group ('module')
                module = module.replace ("\"", "")
                sys.stdout.write ("#include \"" + module + "\"\n")
                continue
            # enter if-clause
            m = reIfClauseStart.match (line)
            if m is not None:
                ifClauseDepth = ifClauseDepth + 1
                sys.stdout.write ("\n")
                continue
            # leave if-clause
            if ifClauseDepth > 0:
                m = reIfClauseEnd.match (line)
                if m is not None:
                    ifClauseDepth = ifClauseDepth - 1
                    if commentDepth > ifClauseDepth:
                        previousBlock = ''
                        currentBlock  = ''
                    sys.stdout.write ("\n")
                    continue
            # Doxygen comment
            m = reCommentStart.match (line)
            if m is not None:
                comment = m.group ('comment')
                sys.stdout.write ("///" + comment + "\n")
                currentBlock = 'comment'
                commentDepth = ifClauseDepth
                m = reParamDoc.search (line)
                if m is not None:
                    param = m.group ('param')
                    params.append (param)
                continue
            # if previous block was a Doxygen comment process
            # supported following blocks such as variable setting
            # and function definition optionally only the one
            # inside the if-case of an if-else-clause
            if previousBlock == 'comment':
                # function
                m = reFunctionStart.match (line)
                if m is not None:
                    name = m.group ('name')
                    sys.stdout.write ("function " + name + " (")
                    for i in range (0, len (params)):
                        if i > 0:
                            sys.stdout.write (", ")
                        sys.stdout.write ("in " + params [i])
                    sys.stdout.write (");\n")
                    currentBlock = 'function'
                    params = []
                    continue
            # unhandled lines...
            if line != '':
                if previousBlock == 'comment':
                    # prevent comments that are not associated with any
                    # processed block to be merged with subsequent comments
                    sys.stdout.write ("class COMMENT_DUMPED_BY_DOXYGEN_FILTER;\n")
                else:
                    sys.stdout.write ("\n")
                previousBlock = ''
            else:
                sys.stdout.write ("\n")
        else:
            sys.stdout.write ("\n")
    # close input file
    f.close ()
    # done
    sys.exit (0)
