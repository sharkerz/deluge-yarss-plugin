#
# common.py
#
# Copyright (C) 2012 Bro
#
# Based on work by:
# Copyright (C) 2009 Camillo Dell'mour <cdellmour@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

import pkg_resources
import datetime
import os, sys

def get_version():
    """
    Returns the program version from the egg metadata

    :returns: the version of Deluge
    :rtype: string

    """
    return pkg_resources.require("YaRSS2")[0].version

def is_running_from_egg():
    import pkg_resources, sys
    egg = pkg_resources.require("YaRSS2")[0]
    return egg.location.endswith(".egg")

def get_deluge_version():
    import deluge.common
    return deluge.common.get_version()

def get_resource(filename, path="data"):
    return pkg_resources.resource_filename("yarss2", os.path.join(path, filename))

def get_default_date():
    return datetime.datetime(datetime.MINYEAR, 1, 1, 0, 0, 0, 0)

def get_current_date():
    return datetime.datetime.now()

def get_current_date_in_isoformat():
    return get_current_date().strftime("%Y-%m-%dT%H:%M:%S")

def isodate_to_datetime(date_in_isoformat):
    try:
        return datetime.datetime.strptime(date_in_isoformat, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return get_default_date()

def string_to_unicode(string):
    if type(string) is unicode:
        # Already unicode
        return string
    try:
        return string.decode("utf-8")
    except:
        warn("string_to_unicode: Failed to convert '%s' to unicode." % string)
        return string

def get_new_dict_key(dictionary, string_key=True):
    """Returns the first unused key in the dictionary.
    string_key: if True, use strings as key, else use int
    """
    key = 0
    while dictionary.has_key(str(key) if string_key else key):
        key += 1
    return str(key) if string_key else key

def get_value_in_selected_row(treeview, store, column_index=0):
    """Helper to get the value at index 'index_column' of the selected element
    in the given treeview.
    return None of no item is selected.
    """
    tree, tree_id = treeview.get_selection().get_selected()
    if tree_id:
        value = store.get_value(tree_id, column_index)
        return value
    return None

def write_to_file(filepath, content):
    """Used for debugging"""
    if "%d" in filepath:
        count = 0
        while os.path.isfile(filepath % count):
            count += 1
        filepath = filapath % count
    local_file = open(filepath, "w")
    local_file.write(content)
    local_file.close()

def read_file(filepath):
    if not os.path.isfile(filepath):
        return None
    f = open(filepath, "r")
    content = f.read()
    return content

def method_name():
    return sys._getframe(3).f_code.co_name

def filename(level=3):
    fname = sys._getframe(level).f_code.co_filename
    fname = os.path.splitext(os.path.basename(fname))[0]
    return fname

def linenumber(level=3):
    return sys._getframe(level).f_lineno

def get_exception_string():
    import traceback
    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    return ''.join('!! ' + line for line in lines)


def dicts_equals(dict1, dict2, debug=False):
    """Compares two dictionaries, checking that they have the same key/values"""
    ret = True
    if not (type(dict1) is dict and type(dict2) is dict):
        print "dicts_equals: Both arguments are not dictionaries!"
        return False

    key_diff = set(dict1.keys()) - set(dict2.keys())
    if key_diff:
        if debug:
            print "dicts_equals: Keys differ:", key_diff
        return False
    for key in dict1.keys():
        if type(dict1[key]) is dict:
            if not dicts_equals(dict1[key], dict2[key], debug=debug):
                ret = False
        else:
            # Compare values
            if dict1[key] != dict2[key]:
                if debug:
                    print "Value for key '%s' differs. Value1: '%s', Value2: '%s'" % (key, dict1[key], dict2[key])
                ret = False
    return ret

def get_path_completion(value):
    """
    Takes a path value and returns the available completions.

    :param value: path to complete
    :type value: string
    :returns: a sorted list of available completions for the input value
    :rtype: list

    """
    dirname = os.path.dirname(value)
    basename = os.path.basename(value)
    matching_dirs = []

    def get_subdirs(dirname):
        try:
            return os.walk(dirname).next()[1]
        except StopIteration:
            # Invalid dirname
            return []
    dirs = get_subdirs(dirname)

    # No completions available
    if not dirs:
        return []

    for s in dirs:
        if s.startswith(basename):
            p = os.path.join(dirname, s)
            if not p.endswith("/"):
                p += "/"
            matching_dirs.append(p)
    return sorted(matching_dirs)


class GeneralSubsConf:
    """General subscription config"""
    DISABLED = u"False"
    ENABLED = u"True"
    DEFAULT = u"Default"

    def __init__(self):
        pass

    def get_boolean(self, value):
        """input value should not be GeneralSubsConf.DEFAULT"""
        return False if value == GeneralSubsConf.DISABLED else True

    def bool_to_value(self, enabled, default):
        if default:
            return GeneralSubsConf.DEFAULT
        elif enabled:
            return GeneralSubsConf.ENABLED
        else:
            return GeneralSubsConf.DISABLED

class TorrentDownload(dict):
    def __init__(self, d={}):
        self["filedump"] = None
        self["error_msg"] = None
        self["torrent_id"] = None
        self["success"] = True
        self["url"] = None
        self["is_magnet"] = False
        self["cookies_dict"] = None
        self.update(d)

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, name, value):
        self[name] = value

    def set_error(self, error_msg):
        self["error_msg"] = error_msg
        self["success"] = False

    def to_dict(self):
        return self.copy()
