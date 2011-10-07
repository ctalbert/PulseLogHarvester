 ***** BEGIN LICENSE BLOCK *****
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
from optparse import OptionParser

class HarvesterOptions(OptionParser):

    def __init__(self, **kwargs):
        OptionParser.__init__(self)
        defaults = {}
        
        self.add_option('--tree', action="store", type='string',
            dest='tree', help = 'Comma separated list of trees to watch for pulling builds, default mozilla-central')
        defaults['tree'] = 'mozilla-central'

        self.add_option('--platforms', action="store", type = "string",
            dest='platforms', help = "Comma separated list of platforms to pull builds for - defaults to all")
        defaults['platforms'] = 'linux,linux64,win32,win64,macosx,macosx64'
        
        self.add_option('--buildtype', action="store", type="string",
            dest="buildtype", help = "Either opt,dbg build to pull from, defaults to all")
        defaults["buildtype"] = 'debug,opt'
        
        self.add_option('--testlist', action='store', type='string',
            dest='testlist', help="Comma separated list of test types to harvest logs for, defaults to talos")
        defaults["testlist"] = 'talos'

        self.set_defaults(**defaults)
        
class Harvester():
    """
    Each parameter is an array of elements
    """
    def __init__(self, tree, platforms, buildtype, testlist, async=False):

        self.testlist = testlist
        self.monitor = start_pulse_monitor(label="harvester@mozilla.com|PulseTestLogFetcher",
                                   testCallback=self.on_test_complete, tree=tree,
                                   platform=platforms, buildtype=buildtype)
        if not async:
            self.monitor.join()
    
    def on_test_complete(self, testdata):
        print "---------------------------------------------------------"
        print "Got Test data %s" % testdata
        print "---------------------------------------------------------"
        
        try:
            if testdata['test'] in self.testlist:
                self.handle_log(testdata)
        except:
            print "Threw exception while handling test data %s: %s" % (sys.exc_info()[:2])
            raise

    def handle_log(self, testdata):
        print "Here is where you handle the test data, right now, we dump log to stdout"
        print "LogURL: %s" % testdata["logurl"]
        response = urllib2.urlopen(testdata["logurl"])
        logdata = response.read()
        print "------ BEGINNING LOG DUMP -----"
        print logdata
        print "------ ENDING LOG DUMP -------"
    

def main():
    parser = HarvesterOptions()
    options, args = parser.parse_args()
    tree = options.tree.split(',')
    platforms = options.platforms.split(',')
    buildtype = options.buildtype.split(',')
    testlist = options.testlist.split(',')
    h = Harvester(tree, platforms, buildtype, testlist)
    
if __name__ == "__main__":
    main()
