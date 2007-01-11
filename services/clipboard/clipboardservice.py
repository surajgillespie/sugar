# Copyright (C) 2006, Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import logging
import gobject
import dbus
import dbus.service
from sugar import env
from sugar import util
from clipboardobject import ClipboardObject, Format

NAME_KEY = 'NAME'
PERCENT_KEY = 'PERCENT'
ICON_KEY = 'ICON'
PREVIEW_KEY = 'PREVIEW'
ACTIVITY_KEY = 'ACTIVITY'
FORMATS_KEY = 'FORMATS'

class ClipboardDBusServiceHelper(dbus.service.Object):

    _CLIPBOARD_DBUS_INTERFACE = "org.laptop.Clipboard"
    _CLIPBOARD_OBJECT_PATH = "/org/laptop/Clipboard"

    def __init__(self, parent):
        self._parent = parent
        self._objects = {}

        bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(self._CLIPBOARD_DBUS_INTERFACE, bus=bus)
        dbus.service.Object.__init__(self, bus_name, self._CLIPBOARD_OBJECT_PATH)

    # dbus methods        
    @dbus.service.method(_CLIPBOARD_DBUS_INTERFACE,
                         in_signature="ss", out_signature="")
    def add_object(self, object_id, name):
        self._objects[object_id] = ClipboardObject(object_id, name)
        self.object_added(object_id, name)
        logging.debug('Added object ' + object_id + ' with name ' + name)

    @dbus.service.method(_CLIPBOARD_DBUS_INTERFACE,
                         in_signature="ssayb", out_signature="", byte_arrays=True)
    def add_object_format(self, object_id, format_type, data, on_disk):
        cb_object = self._objects[object_id]
        cb_object.add_format(Format(format_type, data, on_disk))

        if on_disk:
            logging.debug('Added format of type ' + format_type + ' with path at ' + data)
        else:
            logging.debug('Added in-memory format of type ' + format_type + '.')
                        
        self.object_state_changed(object_id, {NAME_KEY: cb_object.get_name(),
                                  PERCENT_KEY: cb_object.get_percent(),
                                  ICON_KEY: cb_object.get_icon(),
                                  PREVIEW_KEY: cb_object.get_preview(),
                                  ACTIVITY_KEY: cb_object.get_activity()})

    @dbus.service.method(_CLIPBOARD_DBUS_INTERFACE,
                         in_signature="s", out_signature="")
    def delete_object(self, object_id):
        del self._objects[object_id]
        self.object_deleted(object_id)
        logging.debug('Deleted object with object_id ' + object_id)
        
    @dbus.service.method(_CLIPBOARD_DBUS_INTERFACE,
                         in_signature="si", out_signature="")
    def set_object_percent(self, object_id, percent):
        cb_object = self._objects[object_id]
        cb_object.set_percent(percent)
        self.object_state_changed(object_id, {NAME_KEY: cb_object.get_name(),
                                  PERCENT_KEY: percent,
                                  ICON_KEY: cb_object.get_icon(),
                                  PREVIEW_KEY: cb_object.get_preview(),
                                  ACTIVITY_KEY: cb_object.get_activity()})

        logging.debug('Changed object with object_id ' + object_id +
                ' with percent ' + str(percent))

    @dbus.service.method(_CLIPBOARD_DBUS_INTERFACE,
                         in_signature="s", out_signature="a{sv}")
    def get_object(self, object_id):
        cb_object = self._objects[object_id]
        formats = cb_object.get_formats()
        format_types = []
        
        for type, format in formats.iteritems():
            format_types.append(type)
        
        result_dict = {NAME_KEY: cb_object.get_name(),
                PERCENT_KEY: cb_object.get_percent(),
                ICON_KEY: cb_object.get_icon(),
                PREVIEW_KEY: cb_object.get_preview(),
                ACTIVITY_KEY: cb_object.get_activity(),
                FORMATS_KEY: format_types}
        return result_dict

    @dbus.service.method(_CLIPBOARD_DBUS_INTERFACE,
                         in_signature="ss", out_signature="ay")
    def get_object_data(self, object_id, format_type):       
        cb_object = self._objects[object_id]
        formats = cb_object.get_formats()
        return formats[format_type].get_data()
    
    # dbus signals
    @dbus.service.signal(_CLIPBOARD_DBUS_INTERFACE, signature="ss")
    def object_added(self, object_id, name):
        pass

    @dbus.service.signal(_CLIPBOARD_DBUS_INTERFACE, signature="s")
    def object_deleted(self, object_id):
        pass

    @dbus.service.signal(_CLIPBOARD_DBUS_INTERFACE, signature="sa{sv}")
    def object_state_changed(self, object_id, values):
        pass

class ClipboardService(object):
    def __init__(self):
        self._dbus_helper = ClipboardDBusServiceHelper(self)

    def run(self):
        loop = gobject.MainLoop()
        try:
            loop.run()
        except KeyboardInterrupt:
            print 'Ctrl+C pressed, exiting...'
