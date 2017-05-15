#!/usr/bin/env python2
"""
TODO write a description here

Note: python 2 only as next() is not python3 compliant

"""
from __future__ import print_function
import argparse
from collections import deque
import logging
import os
import sys
import time
import threading
try:
    import netaddr
except ImportError as e:
    raise SystemExit("Module 'netaddr' not found. Are you in the virtualenv? See README-venv.md for quickstart instructions.")

###
#
# the payload

import smb_ms17_010


INCREASE_PERCENT = 0.1

log = logging.getLogger(__name__)
sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter())
log.addHandler(sh)
log.setLevel(logging.INFO)


# global object to collect results
res = deque()


class Prober(threading.Thread):
    def __init__(self, target):
        # invoke Thread.__init__
        super(Prober, self).__init__()
        self.target = target

    def run(self):
        # FIXME it does not return - everything goes to stdout
        print("Running against {}".format(self.target))
        smb_ms17_010.check(str(self.target))


def iprange_fromlist(the_list):
    """A generator that returns the content from a file without loading it all in memory"""
    with open(the_list) as f:
        for line in f.readlines():
            yield line.replace('\n', '')


# fills the queue with new threads
# XXX IMPORTANT:
# 'amount' must be at least as big as the number of subdomains, otherwise the
# remaining will be left out. Reason: there's no replenishing of the queue when
# doing wildcard dns checks.
def fill(d, amount, target_gen):
    for i in range(amount):
        # calls next() on the generator to get the next target
        _target = target_gen.next()
        t = Prober(_target)
        t.start()
        d.append(t)


def main(max_running_threads, outfile, overwrite, infile, iprange):

    #
    ###
    # output management
    #
    print("[+] Output destination: '{}'".format(outfile))
    if os.path.exists(outfile):
        if overwrite is False:
            raise SystemExit(
                "Specified file '{}' exists and overwrite "
                "option (-f) not set".format(outfile))
        else:
            print("[+] Output destination will be overwritten.")
    # print(
    #     "-: queue ckeck interval increased by {}%\n.: "
    #     "no change\n".format(INCREASE_PERCENT))

    #
    ###
    #

    print("[+] Press CTRL-C to gracefully stop...")

    #
    ###
    # Begin

    # this is the starting value - it will adjust it according to depletion
    # rate
    sleep_time = 0.5

    # the main queue containing all threads
    d = deque()

    if infile is None:
        target_gen = netaddr.IPNetwork(iprange).iter_hosts()
        print("[+] Will probe all IPs in the range {}".format(iprange))
    else:
        if not os.path.exists(infile):
            raise SystemExit("{} not found".format(infile))
        target_gen = iprange_fromlist(infile)
        print("[+] Will probe all IPs contained in '{}'".format(infile))

    # pre-loading of queue
    print("[+] Probing starting...")
    try:
        # fill the queue ip to max for now
        #    nsvrs = dns.resolver.query(dom, 'NS')
        # ns = str(nsvrs[random.randint(0, len(nsvrs)-1)])[:-1]
        fill(d, max_running_threads, target_gen)
        running = True
    except StopIteration:
        running = False
    except KeyboardInterrupt:
        running = False

    previous_len = len(d)
    while running:
        try:
            time.sleep(sleep_time)
            # go through the queue and remove the threads that are done
            for el in range(len(d)):
                _t = d.popleft()
                if _t.is_alive():
                    # put it back in the queue until next iteration
                    d.append(_t)

            # calculate how fast the queue has been changing
            delta = previous_len - len(d)
            rate = delta / sleep_time

            if rate > 0 and delta > max_running_threads / 10:
                sleep_time -= (sleep_time * INCREASE_PERCENT)
            else:
                sleep_time += (sleep_time * INCREASE_PERCENT)

            fill(d, delta, target_gen)
            previous_len = len(d)

        except KeyboardInterrupt:
            print("\n[+] Probing stopped.")
            running = False
        except StopIteration:
            print("\n[+] Probing done.")
            running = False
        finally:
            sys.stdout.flush()

    print("[+] Waiting for all threads to finish...")
    # waiting for all threads to finish, popping them one by one and join()
    # each...
    for el in range(len(d)):
        t = d.popleft()
        t.join()
    print("[+] Saving results to {}...".format(outfile))
    with open(outfile, 'w') as f:
        for r in res:
            f.write('{}\n'.format(r))
    print("[+] Done.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("max_running_threads", type=int)
    parser.add_argument("savefile", default="out.txt")
    parser.add_argument(
        "-f", "--force-overwrite", default=False,
        action='store_true')
    parser.add_argument(
        "-i", "--use-list", help="Reads the list from a file",
        default=None)
    parser.add_argument("-r", "--ip-range", default=None)
    parser.add_argument('-d', '--debug', action='store_true')
    args = parser.parse_args()

    if args.ip_range is None and args.use_list is None:
        raise SystemExit("Pleas specify either an ip range or a list")

    if args.debug:
        log.setLevel(logging.DEBUG)
        log.debug("Debug logging enabled")

    main(
        args.max_running_threads,
        args.savefile,
        args.force_overwrite,
        args.use_list,
        args.ip_range,
    )
