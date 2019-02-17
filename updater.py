#!/usr/bin/env python3
# Original Script by Michael Shepanski (2013-08-01, python 2)
# Updated to work with Python 3
# Updated to use DigitalOcean API v2

# ChangeLog
# 17/02/2019 Pedro Ruiz - Get domains from a json file -

import argparse
import os
import ipaddress
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from functools import wraps

CHECKIP_URL = "http://ipinfo.io/ip"
APIURL = "https://api.digitalocean.com/v2"


def retry(times=-1, delay=0.5, errors=(Exception,)):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            count = 0
            while True:
                try:
                    count = count + 1
                    return f(*args, **kwargs)
                except errors as e:
                    if count == times:
                        raise e
                    time.sleep(delay)
        return wrapper
    return decorator


def create_headers(token, extra_headers=None):
    rv = {'Authorization': "Bearer %s" % (token)}
    if extra_headers:
        rv.update(extra_headers)
    return rv


@retry(times=5, delay=1.0, errors=(urllib.error.HTTPError,))
def get_url(url, headers=None):
    if headers:
        req = urllib.request.Request(url, headers=headers)
    else:
        req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as file:
        data = file.read()
        return data.decode('utf8')


@retry(times=5, delay=1.0, errors=(urllib.error.HTTPError,))
def put_url(url, data, headers):
    req = urllib.request.Request(url, data=data, headers=headers)
    req.get_method = lambda: 'PUT'
    with urllib.request.urlopen(req) as file:
        data = file.read()
        return data.decode('utf8')


def get_external_ip(expected_rtype):
    """ Return the current external IP. """
    external_ip = get_url(CHECKIP_URL).rstrip()
    ip = ipaddress.ip_address(external_ip)
    if (ip.version == 4 and expected_rtype != 'A') or (ip.version == 6 and expected_rtype != 'AAAA'):
        raise Exception('Expected Rtype {} but got {}'.format(expected_rtype, external_ip))
    return external_ip


def get_domain(name, token):
    output('Fetching Domain ID for: {}', name)
    url = "%s/domains" % (APIURL)

    while True:
        result = json.loads(get_url(url, headers=create_headers(token)))

        for domain in result['domains']:
            if domain['name'] == name:
                return domain

        if 'pages' in result['links'] and 'next' in result['links']['pages']:
            url = result['links']['pages']['next']
            # Replace http to https.
            # DigitalOcean forces https request, but links are returned as http
            url = url.replace("http://", "https://")
        else:
            break

    raise Exception("Could not find domain: %s" % name)


def get_record(domain, name, rtype, token):
    output("Fetching Record ID for: {}", name)
    url = "%s/domains/%s/records" % (APIURL, domain['name'])

    while True:
        result = json.loads(get_url(url, headers=create_headers(token)))

        for record in result['domain_records']:
            if record['type'] == rtype and record['name'] == name:
                return record

        if 'pages' in result['links'] and 'next' in result['links']['pages']:
            url = result['links']['pages']['next']
            # Replace http to https.
            # DigitalOcean forces https request, but links are returned as http
            url = url.replace("http://", "https://")
        else:
            break

    raise Exception("Could not find record: %s" % name)


def set_record_ip(domain, record, ipaddr, token):
    print("Updating record {}.{} to {}".format(record['name'], domain['name'], ipaddr))

    url = "%s/domains/%s/records/%s" % (APIURL, domain['name'], record['id'])
    data = json.dumps({'data': ipaddr}).encode('utf-8')
    headers = create_headers(token, {'Content-Type': 'application/json'})

    result = json.loads(put_url(url, data, headers))
    if result['domain_record']['data'] == ipaddr:
        print("Success")


def output(line, *args):
    check = getattr(output, 'suppress', False)
    if check:
        return
    print(line.format(*args))


def loadConfig():
    file = open("/etc/dnsupdater/domain.json" , "r");
    return json.load(file);

def updaterecord(_token, _domain, _record, _rtype):
    try:
        output("Update {}.{}: {}", _record, _domain, datetime.now())
        ipaddr = get_external_ip(_rtype)
        domain = get_domain(_domain, _token)
        record = get_record(domain, _record, _rtype, _token)
        if record['data'] == ipaddr:
            output("Records {}.{} already set to {}.", record['name'], domain['name'], ipaddr)
            return 0

        set_record_ip(domain, record, ipaddr, _token)
        return 0

    except (Exception) as err:
        print("Error: ", err, file=sys.stderr)
        return -1


if __name__ == '__main__':
    config = loadConfig();

    while True :
        for domain in config['domains']:
            updaterecord(domain['token'], domain['domain'], domain['record'], domain['rtype'])

        if int(config['timer']) == 0:
            break;
        else:
            time.sleep(int(config['timer']));
