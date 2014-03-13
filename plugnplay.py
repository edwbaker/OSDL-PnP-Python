import dbus, gobject, avahi, urllib, json
from urllib import urlopen
from dbus import DBusException
from dbus.mainloop.glib import DBusGMainLoop

# Looks for iTunes shares

TYPE = '_sensor._tcp'

def service_resolved(*args):
    print 'service resolved'
    print 'name:', args[2]
    print 'address:', args[7]
    print 'port:', args[8]
    TXTrecords = []
    for array in args[9]:
      TXTrecords.append( "".join(chr(b) for b in array ))
    print 'path:', TXTrecords
    print '\n'
    url = 'http://' + args[7] + ':' + str(args[8]) + '/' + TXTrecords[0]
    print 'fetching: ', url
    jsonurl = urlopen(url)
    text    = json.loads(jsonurl.read())

    print text["sensors"]

def print_error(*args):
    print 'error_handler'
    print args[0]
    
def myhandler(interface, protocol, name, stype, domain, flags):
    print "Found service '%s' type '%s' domain '%s' flags '%s' " % (name, stype, domain, flags)

    if flags & avahi.LOOKUP_RESULT_LOCAL:
            # local service, skip
            pass

    server.ResolveService(interface, protocol, name, stype, 
        domain, avahi.PROTO_UNSPEC, dbus.UInt32(0), 
        reply_handler=service_resolved, error_handler=print_error)

loop = DBusGMainLoop()

bus = dbus.SystemBus(mainloop=loop)

server = dbus.Interface( bus.get_object(avahi.DBUS_NAME, '/'),
        'org.freedesktop.Avahi.Server')

sbrowser = dbus.Interface(bus.get_object(avahi.DBUS_NAME,
        server.ServiceBrowserNew(avahi.IF_UNSPEC,
            avahi.PROTO_UNSPEC, TYPE, 'local', dbus.UInt32(0))),
        avahi.DBUS_INTERFACE_SERVICE_BROWSER)

sbrowser.connect_to_signal("ItemNew", myhandler)

gobject.MainLoop().run()
