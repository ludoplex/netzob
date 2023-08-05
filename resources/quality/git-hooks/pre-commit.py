#!/usr/bin/env python
# -*- coding: utf-8 -*-

#+---------------------------------------------------------------------------+
#|          01001110 01100101 01110100 01111010 01101111 01100010            |
#|                                                                           |
#|               Netzob : Inferring communication protocols                  |
#+---------------------------------------------------------------------------+
#| Copyright (C) 2011-2017 Georges Bossert and Frédéric Guihéry              |
#| This program is free software: you can redistribute it and/or modify      |
#| it under the terms of the GNU General Public License as published by      |
#| the Free Software Foundation, either version 3 of the License, or         |
#| (at your option) any later version.                                       |
#|                                                                           |
#| This program is distributed in the hope that it will be useful,           |
#| but WITHOUT ANY WARRANTY; without even the implied warranty of            |
#| MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the              |
#| GNU General Public License for more details.                              |
#|                                                                           |
#| You should have received a copy of the GNU General Public License         |
#| along with this program. If not, see <http://www.gnu.org/licenses/>.      |
#+---------------------------------------------------------------------------+
#| @url      : http://www.netzob.org                                         |
#| @contact  : contact@netzob.org                                            |
#| @sponsors : Amossys, http://www.amossys.fr                                |
#|             Supélec, http://www.rennes.supelec.fr/ren/rd/cidre/           |
#+---------------------------------------------------------------------------+
import os
import re
import sys
import subprocess
from git import *

ignore_files = [
    "__init__.py",
    "src/netzob/ExternalLibs/xdot.py",
    "test/src/common/xmlrunner.py",
    ".*\.txt", ".*\.rst",
    ".*\.png", ".*\.ico",
    ".*\.xsd", ".*\.xml",
    "resources/*",
    ".*\.pyc",
    "MANIFEST\.in",
    ".*\.po", ".*\.pot",
    "doc/netzob\.1",
    "\.git/*",
    ".*/PKG-INFO",
    ".*/.*\.so",
]

def getFiles():
    currentPath = os.getcwd()
    # First we initialize the repository object
    repository = Repo(currentPath)

    listFile = []
    repositoryIndex = repository.index
    for d in repositoryIndex.diff('HEAD'):
        # Added path
        if d.deleted_file or not d.new_file:
            path = d.a_blob.path
            if path not in listFile:
                listFile.append(path)
    return listFile


def checkPEP8(file):
    localResult = []
    try:
        p = subprocess.Popen(['pep8', '--repeat', '--ignore=E501', file], stdout=subprocess.PIPE)
        out, err = p.communicate()
        localResult.extend(iter(out.splitlines()))
        return localResult
    except Exception as e:
        if "[Errno 2] No such file or directory" in str(e):
            print("[E] PEP8 is not installed.")
        else:
            print("[E] PEP8 does not work, it is probably not installed.\nThe error is : {0}".format(str(e)))
        sys.exit(1)
        

def checkClassDeclation(file):
    localResult = []
    with open(file, 'rb') as f:
        lineNumber = 0
        for line in f:
            if m := re.search('class\s+[^\(]*:', line):
                localResult.append("Old class definition found on {0}".format(m.group()))
    return localResult


def searchForPattern(file, pattern, errorName):
    localResult = []
    with open(file) as fileObject:
        localResult.extend(
            f"{str(errorName)} found at line {str(lineNumber)}"
            for lineNumber, line in enumerate(fileObject, start=1)
            if re.search(pattern, line)
            and not re.search('Thisisnotaconflict', line)
        )
    return localResult


# Verifies only LF ('\n') ended files are committed (no CRLF '\r\n').
def checkForCRLF(file):
    localResult = []
    with open(file, 'rb') as f:
        localResult.extend(
            f"A CRLF ending patterns found at line {str(lineNumber)}"
            for lineNumber, line in enumerate(f, start=1)
            if line.endswith(b"\r\n")
        )
    return localResult


def checkHeader(file):
    header = """#+---------------------------------------------------------------------------+
#|          01001110 01100101 01110100 01111010 01101111 01100010            |
#|                                                                           |
#|               Netzob : Inferring communication protocols                  |
#+---------------------------------------------------------------------------+
#| Copyright (C) 2011-2017 Georges Bossert and Frédéric Guihéry              |
#| This program is free software: you can redistribute it and/or modify      |
#| it under the terms of the GNU General Public License as published by      |
#| the Free Software Foundation, either version 3 of the License, or         |
#| (at your option) any later version.                                       |
#|                                                                           |
#| This program is distributed in the hope that it will be useful,           |
#| but WITHOUT ANY WARRANTY; without even the implied warranty of            |
#| MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the              |
#| GNU General Public License for more details.                              |
#|                                                                           |
#| You should have received a copy of the GNU General Public License         |
#| along with this program. If not, see <http://www.gnu.org/licenses/>.      |
#+---------------------------------------------------------------------------+
#| @url      : http://www.netzob.org                                         |
#| @contact  : contact@netzob.org                                            |
#| @sponsors : Amossys, http://www.amossys.fr                                |
#|             Supélec, http://www.rennes.supelec.fr/ren/rd/cidre/           |
#+---------------------------------------------------------------------------+"""
    header2 = header.replace("#", "//")  # For C files
    header3 = header.replace("#", "")     # For other
    headerGlade = header3.replace("---------------------------------------------------------------------------", "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")     # For other
    with open(file, 'rb') as f:
        data = f.read()
    if header not in data and header2 not in data and header3 not in data:
        if file.startswith(os.path.join("src", "netzob_plugins")):  # Plugin
            headersPlugin = header.split("2011 Georges Bossert and Frédéric Guihéry                   |")
            if headersPlugin[0] in data and headersPlugin[1] in data:
                return []
        return ["The header has not been found in file"]
    return []


def checkFile(file):
    results = {}

    if file.endswith("__init__.py"):
        return results

    if file.endswith(".pyc"):
        return results

    # Verify no '<<<' and or conflicts info are commited
    results['Conflicts'] = searchForPattern(file, '<<<<<<', 'hints of untreated conflicts')  # Thisisnotaconflict

    for ignore in ignore_files:
        if re.match(ignore, file):
            return results

    # Verify no CRLF is used in source
    results['CRLF'] = checkForCRLF(file)

    # Verify the header is valid
    results['Header'] = checkHeader(file)

    # Check against PEP8 rules for python files
    if os.path.splitext(file)[-1] == ".py":
        results['PEP8'] = checkPEP8(file)
        results['Old Class'] = checkClassDeclation(file)

    return results

def verifyResults(results):
    result = 0
    for f in list(results.keys()):
        resultFile = results[f]
        if len(resultFile) > 0:
            ruleNames = list(resultFile.keys())
            localResult = 0

            errorForCurrentFile = []
            for ruleName in ruleNames:
                ruleErrors = resultFile[ruleName]
                if ruleErrors is not None and len(ruleErrors) > 0:
                    errorForCurrentFile.extend(
                        "[E]\t %s : %s" % (ruleName, ruleError)
                        for ruleError in ruleErrors
                    )
                    result = 1
                    localResult = 1

            if errorForCurrentFile:
                print(f"[I] File {f}:")
                for err in errorForCurrentFile:
                    print(err)

    return result

def analyze(providedFiles):

    files = []
    if providedFiles is None:
        # Retrieve all the files to analyze
        print("[I] Retrieve all the files to analyze from the staged area.")
        tmp_files = getFiles()
        # Filters directories which could appears in files due to submodules creation
        # TODO : should be invastigated in details why this could happen
        files.extend(f for f in tmp_files if os.path.isfile(f))
    else:
        print("[I] Retrieve all the file to analyze from the command line arguments.")
        filesToAnalyze = getFilesFromListOfPath(providedFiles)

        for fileToAnalyze in filesToAnalyze:
            if os.path.isfile(fileToAnalyze):
                try:
                    test = open(fileToAnalyze)
                    test.close()
                    files.append(fileToAnalyze)
                except:
                    print(f"[E] File {fileToAnalyze} exists but is not readable.")

    globalResults = {
        fileToAnalyze: checkFile(fileToAnalyze) for fileToAnalyze in files
    }
    # Compute the final result (0=sucess, 1=cannot commit)
    result = verifyResults(globalResults)
    if result == 0:
        print("[I] No error found, commit allowed.")
    else:
        print("[E] Errors founds, commit not allowed.")
    sys.exit(result)

def getFilesFromListOfPath(paths):
    result = []
    for p in paths:
        if os.path.isfile(p):
            result.append(p)
        elif os.path.isdir(p):
            subfiles = os.listdir(p)
            toAnalyze = [os.path.join(p, s) for s in subfiles]
            subfilesResult = getFilesFromListOfPath(toAnalyze)
            result.extend(subfilesResult)
    return result

if __name__ == '__main__':

    filesToAnalyze = sys.argv[1:] if (len(sys.argv) > 1) else None
    # Execute the analysis
    analyze(filesToAnalyze)
