import concurrent.futures
import json
import os
import sys
import urllib.request

from urllib.parse import urlparse



host_list_filename = sys.argv[1]
path_list_filename = sys.argv[2]

request_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=100)
state_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)

state = {}
state_file_name = "current_state.json"

def save_state():
    with open (state_file_name, "w") as f:
        json.dump(state, f)


def clean_lines(lines):
    lines = [line.strip() for line in lines]
    lines = list(filter(None, lines))
    lines = list(filter(len, lines))
    return lines

def get_host_list(filename):
    with open(filename) as host_file:
        lines = host_file.readlines()
        lines = clean_lines(lines)
        return lines

def get_path_list(filename):
    with open(filename) as path_file:
        lines = path_file.readlines()
        lines = clean_lines(lines)
        return lines

def add_entry(host, path, status_code):
    if not host in state:
        state[host] = {}

    host_entry = state[host]
    if not status_code in host_entry:
        host_entry[status_code] = []

    host_entry[status_code].append(path)
    save_state()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

def process_request(host, path):
    parsed_host = urlparse(host)
    url = parsed_host.scheme + "://" + parsed_host.hostname
    if parsed_host.port:
        url += ":" + str(parsed_host.port)
    url += "/" + path

    status_code = 0
    try:
        response = opener.open(url, timeout = 10)
        status_code = response.status
    except urllib.error.HTTPError as e:
        status_code = e.status
    except Exception as e:
        print(type(e).__name__)
        print(e)

    if status_code > 0:
        state_thread_pool.submit(add_entry, host, path, status_code)


futures = []
for path in get_path_list(path_list_filename):
    for host in get_host_list(host_list_filename):
        # process_request(host, path)
        futures.append(
                request_thread_pool.submit(process_request, host, path))

concurrent.futures.wait(futures)

