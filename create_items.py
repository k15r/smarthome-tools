#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json
from argparse import ArgumentParser

DPT = {
    '1b': '1',
    '2b': '2',
    '4b': '3',
    '8b': '5',
    '1B': '5',
    '2B': '8',
    '3B': '232',
    '4B': '13',
    '14B': '16',
}

TRANSLATION_TABLE = {
    ord(u'ä'): u'ae',
    ord(u'ö'): u'oe',
    ord(u'ü'): u'ue',
    ord(u'ß'): u'ss',
}


def print_item(key, item, level):
    prefix = "\t" * (level)

    if isinstance(item, dict):
        translated_key = key.decode('utf8').translate(TRANSLATION_TABLE)
        safe_key = re.sub(r'[^abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_]','_',translated_key)
        safe_key = re.sub(r'_+','_',safe_key)
        print "{}{}{}{}".format('\t'*(level-1), '[' *level , safe_key, ']' * level )
        print "{}name = {}".format(prefix, translated_key)

        if item.get('room'):
            print "{}sv_page = room".format(prefix)
        elif key == "level":
                print "{}type = num".format(prefix)
                print "{}visu_acl = rw".format(prefix)
        elif [key for key in item.keys() if 'knx' in key.lower()]:
            if [key for key in item.keys() if 'level' in key.lower()]:
                print "{}type = bool".format(prefix)
                print "{}visu_acl = rw".format(prefix)
                print "{}sv_widget = {{{{ device.dimmer('item', 'item.name', 'item', 'item.level') }}}}".format(prefix)
            else:
                print "{}type = bool".format(prefix)
                print "{}visu_acl = rw".format(prefix)
                print "{}sv_widget = {{{{ basic.switch('item', 'item.name') }}}}".format(prefix)
        for a, b in { a:b for (a,b) in item.items() if isinstance(b, basestring)}.items():
            print_item(a, b, level + 1)
        for a, b in { a:b for (a,b) in item.items() if isinstance(b, dict)}.items():
            print_item(a, b, level + 1)
    else:
        if key == "knx_dpt":
            item = DPT[item]
        prefix = "\t" * (level-1)
        print "{}{} = {}".format(prefix, key, item)


def parse_commandline():
    parser = ArgumentParser()
    parser.add_argument("--file-name",
                        required=True,
                        help="File to read from")

    return parser.parse_args()



def main():
    options = parse_commandline()
    with open(options.file_name) as config:
        lines = config.readlines()

    status_re = re.compile('^Status (.*)')
    switch_re = re.compile('^Schalten (.*)')
    level_re = re.compile('^Dimmen (.*)')
    up_down_re = re.compile(r'(.*) Auf/Ab')
    stop_re = re.compile(r'(.*) Stop')

    items = {}
    addr_name_dpt_re = re.compile(r'^(?P<address>\d+/\d+/\d+) (?P<description>.*) (?P<type>1b|2b|4b|8b|1B|2B|3B|4B|14B)$')
    for line in lines:
        line = line.strip()
        item_match = addr_name_dpt_re.match(line)
        if item_match:
            description = item_match.group('description')
            address = item_match.group('address')
            datatype = item_match.group('type')
            room_match = re.search(r'(Wohnen|Bad|Büro|Küche|Essen|Technikraum|Ankleide|Schlafen|Flur|WC)',description)
            description = re.sub(r'(Wohnen|Bad|Büro|Küche|Essen|Technikraum|Ankleide|Schlafen|Flur|WC)','', description).strip()
            description = re.sub(r'\s+', ' ', description)
            room = room_match.group(1) if room_match else 'Allgemein'
            status = status_re.match(description)
            switch = switch_re.match(description)
            level = level_re.match(description)
            up_down = up_down_re.match(description)
            stop = stop_re.match(description)
            room_items = items.get(room,{ 'room' : True})
            if status:
                temp = room_items.get(status.group(1), {})
                temp['knx_status'] = item_match.group(1)
                temp['knx_dpt'] = item_match.group(3)
                room_items[status.group(1)] = temp
            elif switch:
                temp = room_items.get(switch.group(1), {})
                temp['knx_send'] = item_match.group(1)
                temp['knx_dpt'] = item_match.group(3)
                room_items[switch.group(1)] = temp
            elif up_down:
                temp = room_items.get(up_down.group(1), {})
                temp['up_down'] = {
                    'knx_send': item_match.group(1),
                    'knx_dpt': item_match.group(3)
                }
                room_items[up_down.group(1)] = temp
            elif stop:
                temp = room_items.get(stop.group(1), {})
                temp['stop'] = {
                    'knx_send': item_match.group(1),
                    'knx_dpt': item_match.group(3)
                }
                room_items[stop.group(1)] = temp
            elif level:
                temp = room_items.get(level.group(1), {})
                temp['level'] = {
                    'knx_send': item_match.group(1),
                    'knx_dpt': item_match.group(3)
                }
                room_items[level.group(1)] = temp
            else:
                temp = room_items.get(description, {})
                temp['knx_reply'] = item_match.group(1)
                temp['knx_dpt'] = item_match.group(3)
                room_items[description] = temp
            items[room] = room_items



    for a,b in items.iteritems():
        print_item(a, b, 1)


if __name__ == "__main__":
    main()
