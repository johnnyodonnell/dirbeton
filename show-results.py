import json
import sys


def main():
    results_filename = sys.argv[1]

    results = {}
    with open(results_filename) as f:
        results = json.load(f)

    printable_results = []

    for host in results:
        host_results = results[host]
        host_map = None
        for status_code_str in host_results:
            status_code = int(status_code_str)
            if (status_code >= 200) and (status_code < 400):
                if host_map is None:
                    host_map = {"host": host, "results": []}

                host_map["results"].append({
                    "status": status_code,
                    "paths": host_results[status_code_str]
                    })
        if host_map:
            printable_results.append(host_map)

    for host_map in printable_results:
        host = host_map["host"]
        print(host)
        results = host_map["results"]
        for result in results:
            status_code = result["status"]
            print("--- " + str(status_code) + " ---")
            paths = result["paths"]
            for path in paths:
                print(path)
        print("") # Empty line

main()

