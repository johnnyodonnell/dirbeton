import json
import sys


http_ports = {80, 8080}
https_ports = {443, 8443}

def parse_and_add(raw_arg, port_set):
    port_list = raw_arg.split(",")
    for addl_port in port_list:
        port_set.add(int(addl_port))

def main():
    print("fetch-web-endpoints <additional http ports> <additional https ports>")

    if (len(sys.argv) > 1):
        parse_and_add(sys.argv[1], http_ports)
    if (len(sys.argv) > 2):
        parse_and_add(sys.argv[2], https_ports)

    current_state = {}
    with open("current_state.json") as f:
        current_state = json.load(f)

    hosts = current_state["hosts"]
    for address in hosts:
        host = hosts[address]
        if ("status" in host) and (host["status"] == "up") and ("ports" in host):
            ports = host["ports"]
            if "tcp" in ports:
                tcp_ports = ports["tcp"]
                for portid in tcp_ports:
                    port = tcp_ports[portid]
                    if ("state" in port) and (port["state"] == "open"):
                        if int(portid) in http_ports:
                            print("http://" + address + ":" + portid)
                        if int(portid) in https_ports:
                            print("https://" + address + ":" + portid)

main()

