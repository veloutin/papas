#!/usr/bin/env python
import os, sys
os.environ["DJANGO_SETTINGS_MODULE"] = "apmanager.settings"
from apmanager import settings

from pyinotify import WatchManager, Notifier, ProcessEvent, EventsCodes
from apmanager.accesspoints.apcommands import CommandExec
from apmanager.accesspoints.models import AccessPoint
from apmanager import utils

def Monitor(path):
    class PCreate(ProcessEvent):
        ACTIONS = (
            (settings.COMMAND_WATCH_DIR, 'command'),
            (settings.AP_REFRESH_WATCH_DIR, 'ap'),
        )
        def dispatch_process(self, func, event):
            for action in self.ACTIONS:
                if os.path.samefile(event.path,action[0]):
                    tocall = 'process_'+action[1]+'_'+func
                    if hasattr(self,tocall) and callable(getattr(self,tocall)):
                        return getattr(self,tocall)(event)
            print "Unhandled Event: ", event
            return None
        
        def process_command_IN_CREATE(self,event):
            f = os.path.join(event.path, event.name)
            if os.path.isfile(f):
                os.unlink(f)
            print 'processing command exec: ' + event.name
            try:
                a = CommandExec.objects.get(pk=event.name)
                a.execute() 
            except Exception, e:
                print e

        def process_ap_IN_CLOSE(self,event):
            print 'processing ap refresh: ' + event.name
            try:
                a = AccessPoint.objects.get(pk=event.name)
                a.refresh_clients()
            except Exception, e:
                print e
            
        def process_IN_CREATE(self, event):
            return self.dispatch_process('IN_CREATE',event)

        def process_IN_CLOSE(self,event):
            return self.dispatch_process('IN_CLOSE',event)

    wm = WatchManager()
    notifier = Notifier(wm, PCreate())
    wm.add_watch(path, EventsCodes.IN_CREATE | EventsCodes.IN_CLOSE_WRITE , None, True)

    try:
        while 1:
            notifier.process_events()
            if notifier.check_events():
                notifier.read_events()
    except KeyboardInterrupt:
        notifier.stop()
        return


if __name__ == '__main__':
    if "--daemon" in sys.argv[1:]:
        utils.daemonize()

	print "using default path, ", settings.WATCH_DIR
	Monitor(settings.WATCH_DIR)
