import concurrent.futures
import json
import datetime
import os
import sys
import urllib.request

from urllib.parse import urlparse



if (len(sys.argv) < 3):
    print("dirbeton <host_list> <path_list>")
    exit()

host_list_filename = sys.argv[1]
path_list_filename = sys.argv[2]


request_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=100)
state_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)

state = {}
state_file_name = "results.json"
state_file_name_10m = "results_10m.json"
last_minute = -1

def save_state():
    with open(state_file_name, "w") as f:
        json.dump(state, f)

    # Every 10 minutes, save to similarly named file
    now = datetime.datetime.now()
    if ((now.minute % 10) == 0) and (now.minute != last_minute):
        last_minute = now.minute
        with open(state_file_name_10m, "w") as f:
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

def process_request(host, path, path_list, depth = 0):
    parsed_host = urlparse(host)
    url = parsed_host.scheme + "://" + parsed_host.hostname
    if parsed_host.port:
        url += ":" + str(parsed_host.port)
    url += "/" + path

    response = None
    try:
        response = opener.open(url, timeout = 10)
    except urllib.error.HTTPError as e:
        response = e
    except Exception as e:
        print(type(e).__name__)
        print(e)

    if not response is None:
        status_code = response.status
        state_thread_pool.submit(add_entry, host, path, status_code)

        if (status_code >= 300) and (status_code < 400) and (depth < 5):
            location = response.getheader("Location")
            if location == ("/" + path + "/"):
                futures = []
                for next_level in path_list:
                    new_path = path + "/" + next_level
                    futures.append(
                            request_thread_pool.submit(
                                process_request,
                                host,
                                new_path,
                                path_list,
                                depth + 1))
                concurrent.futures.wait(futures)


futures = []
path_list = get_path_list(path_list_filename)
for path in path_list:
    for host in get_host_list(host_list_filename):
        # process_request(host, path, path_list)
        futures.append(
                request_thread_pool.submit(process_request, host, path, path_list))

concurrent.futures.wait(futures)

