# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Pulse Log Harvester.
#    
# The Initial Developer of the Original Code is
# Mozilla foundation
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Clint Talbert <ctalbert@mozilla.com>
#   Stephen Lewchuk <slewchuk@mozilla.com>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

from pulsebuildmonitor import start_pulse_monitor
import os
import sys
import threading
import shutil
import urllib2
import json
import gzip
import StringIO
from optparse import OptionParser

class HarvesterOptions(OptionParser):

    def __init__(self, **kwargs):
        OptionParser.__init__(self)
        defaults = {}
        
        self.add_option('--tree', action="store", type='string',
            dest='tree', help = 'Comma separated list of trees to watch for pulling builds, default mozilla-central')
        defaults['tree'] = 'mozilla-central'

        self.add_option('--platforms', action="store", type = "string",
            dest='platforms', help = "Comma separated list of platforms to pull builds for - defaults to all with blank spec")
        
        self.add_option('--buildtype', action="store", type="string",
            dest="buildtype", help = "Either opt,dbg build to pull from, defaults to all with blank spec")
        
        self.add_option('--testlist', action='store', type='string',
            dest='testlist', help="Comma separated list of test types to harvest logs for, defaults to all with blank spec")

        self.add_option('--strip-non-talos', action='store_true',
            dest='strip_non_talos', help="Flag to drop non-talos tests, defaults to false, should not be used with --strip-talos")
        defaults['strip_non_talos'] = False

        self.add_option('--strip-talos', action='store_true',
            dest='strip_talos', help="Flag to drop talos tests, defaults to false, should not be used with --strip-non-talos")
        defaults['strip_talos'] = False

        self.add_option('--dump', action='store_true',
            dest='dump', help="Flag to pull logs and dump to stdin - will unzip the file - defaults to flase")

        self.add_option('--log-destination', action='store', type = 'string',
            dest='log_dest', help="Location to store downloaded logs - defaults to ./logs/")
        defaults['log_dest'] = "./logs/"

        self.set_defaults(**defaults)
        
class Harvester():
    """
    Each parameter is an array of elements
    """
    def __init__(self, tree, platforms, buildtype, testlist, log_dest, strip_talos, strip_non_talos, dump, async=False):

        print (tree, platforms, buildtype, testlist, strip_talos, strip_non_talos)

        self.testlist = testlist
        self.strip_talos = strip_talos
        self.strip_non_talos = strip_non_talos
        self.log_dest = log_dest
        self.dump = dump

        self.log_dest = os.path.abspath(log_dest)
        if not os.path.exists(self.log_dest):
            os.makedirs(self.log_dest)

        self.monitor = start_pulse_monitor(label="harvester@mozilla.com|PulseTestLogFetcher",
                                   testCallback=self.on_test_complete, tree=tree,
                                   platform=platforms, buildtype=buildtype, includeTalos=True)
        if not async:
            self.monitor.join()
    
    def on_test_complete(self, testdata):
        print "---------------------------------------------------------"
        print "Got Test data for %s" % testdata['buildername']
        print "---------------------------------------------------------"
        
        try:
            if testdata['talos'] and self.strip_talos:
                return
            if not testdata['talos'] and self.strip_non_talos:
                return
            if not self.testlist or testdata['test'] in self.testlist:
                self.handle_log(testdata)
        except:
            print "Threw exception while handling test data %s: %s" % (sys.exc_info()[:2])
            raise

    def handle_log(self, testdata):
        print "Handling log: %s" % testdata["buildername"]
        response = urllib2.urlopen(testdata["logurl"])
        logdata = response.read()

        outfilename = testdata["logurl"].replace("_","-").replace("/","_").replace(":","")
        outpath = os.path.join(self.log_dest, outfilename)
        print "Log written to: %s" % outpath

        with open(outpath,'w') as outfile:
            outfile.write(logdata)

        outpath_log = outpath[:outpath.rfind('.')] + ".json"
        with open(outpath_log,'w') as outfile:
            outfile.write(json.dumps(testdata))

        if self.dump:
            print "------ BEGINNING LOG DUMP -----"
            if testdata['logurl'].endswith('gz'):
                logfile = StringIO(logdata)
                data = gzip.GzipFile(fileobj=logfile)
            else:
                data = logdata
            print data
            print "------ ENDING LOG DUMP -------"

def main():
    parser = HarvesterOptions()
    options, args = parser.parse_args()
    tree = options.tree.split(',')
    platforms = options.platforms and options.platforms.split(',') or None
    buildtype = options.buildtype and options.buildtype.split(',') or None
    testlist = options.testlist and options.testlist.split(',') or None

    h = Harvester(tree, platforms, buildtype, testlist, options.log_dest, options.strip_talos, options.strip_non_talos, options.dump)
    
if __name__ == "__main__":
    main()
