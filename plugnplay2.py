import dbus
from dbus.mainloop.glib import DBusGMainLoop
import avahi
import gobject
import threading
import urllib
from urllib import urlopen
import json
import mysql.connector

gobject.threads_init()
dbus.mainloop.glib.threads_init()

conn = mysql.connector.connect(user='osdl', password='osdlpassword', database='osdl')
cursor = conn.cursor()

class ZeroconfBrowser:
    def __init__(self):
        self.service_browsers = set()
        self.services = {}
        self.lock = threading.Lock()

        loop = DBusGMainLoop(set_as_default=True)
        self._bus = dbus.SystemBus(mainloop=loop)
        self.server = dbus.Interface(
                self._bus.get_object(avahi.DBUS_NAME, avahi.DBUS_PATH_SERVER), 
                avahi.DBUS_INTERFACE_SERVER)

        thread = threading.Thread(target=gobject.MainLoop().run)
        thread.daemon = True
        thread.start()

        self.browse("_sensor._tcp")
        
        self.servicelist = dict()

    def browse(self, service):
        if service in self.service_browsers:
            return
        self.service_browsers.add(service)

        with self.lock:
            browser = dbus.Interface(self._bus.get_object(avahi.DBUS_NAME, 
                    self.server.ServiceBrowserNew(avahi.IF_UNSPEC, 
                            avahi.PROTO_UNSPEC, service, 'local', dbus.UInt32(0))),
                    avahi.DBUS_INTERFACE_SERVICE_BROWSER)

            browser.connect_to_signal("ItemNew", self.item_new)
            browser.connect_to_signal("ItemRemove", self.item_remove)
            browser.connect_to_signal("AllForNow", self.all_for_now)
            browser.connect_to_signal("Failure", self.failure)

    def resolved(self, interface, protocol, name, service, domain, host, 
            aprotocol, address, port, txt, flags):
        #dbus string conversion
        TXTrecords = []
        print type(txt[0])
        
        TXTrecords.append( "".join(chr(b) for b in txt[0] ))

        print TXTrecords

        self.servicelist[name] = {'interface': interface, 'protocol': protocol, 'domain': domain, 'address': address, 'port': port, 'txt': TXTrecords, 'flags': flags}
        print "resolved", interface, protocol, name, service, domain, flags

    def failure(self, exception):
        print "Browse error:", exception

    def item_new(self, interface, protocol, name, stype, domain, flags):
        with self.lock:
            self.server.ResolveService(interface, protocol, name, stype,
                    domain, avahi.PROTO_UNSPEC, dbus.UInt32(0),
                    reply_handler=self.resolved, error_handler=self.resolve_error)
            #self.servicelist[name] = {'interface': interface, 'protocol': protocol, 'stype': stype, 'domain': domain, 'flags': flags}

    def item_remove(self, interface, protocol, name, service, domain, flags):
        del self.servicelist[name]
        print "removed", interface, protocol, name, service, domain, flags

    def all_for_now(self):
        print "all for now"

    def resolve_error(self, *args, **kwargs):
        with self.lock:
            print "Resolve error:", args, kwargs

    def list_service(self):
        return self.servicelist

import time
def main():
    browser = ZeroconfBrowser()
    while True:
        time.sleep(3)
#        for key, value in browser.services.items():
#            print key, str(value)
#            print "Loop"
        services = browser.list_service()
        for key in services:
          base_url = "http://" + services[key]['address'] + ":" + str(services[key]['port'])
          url = base_url  + "/" + str(services[key]['txt'])[7:14]

          jsonurl = urlopen(url)
          text    = json.loads(jsonurl.read())

          for sensor in text["sensors"]:
              for key in sensor:
                 for name in sensor[key]:
                   for attr in name:
                      if (attr == "request_path"):
                        url  = base_url +  name[attr]
                        print url
                        jsonurl = urlopen(url)
                        reading = json.loads(jsonurl.read())
                        print reading
                        print ""

if __name__ == '__main__':
    main()
