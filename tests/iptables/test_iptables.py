import os
import subprocess
import unittest
import xml.etree.ElementTree as ET
from ipaddress import ip_address
from pathlib import Path
from time import sleep

from tests.mock_lapi import MockLAPI
from tests.utils import generate_n_decisions, run_cmd

SCRIPT_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
PROJECT_ROOT = SCRIPT_DIR.parent.parent
BINARY_PATH = PROJECT_ROOT.joinpath("crowdsec-firewall-bouncer")
CONFIG_PATH = SCRIPT_DIR.joinpath("crowdsec-firewall-bouncer.yaml")

SET_NAME_IPV4 = "crowdsec-blacklists"
SET_NAME_IPV6 = "crowdsec6-blacklists"

CHAIN_NAME = "INPUT"


class TestIPTables(unittest.TestCase):
    def setUp(self):
        self.fb = subprocess.Popen([BINARY_PATH, "-c", CONFIG_PATH])
        self.lapi = MockLAPI()
        self.lapi.start()
        return super().setUp()

    def tearDown(self):
        self.fb.kill()
        self.fb.wait()
        self.lapi.stop()
        run_cmd(
            "iptables",
            "-D",
            CHAIN_NAME,
            "-m",
            "set",
            "--match-set",
            SET_NAME_IPV4,
            "src",
            "-j",
            "DROP",
            ignore_error=True,
        )
        run_cmd(
            "ip6tables",
            "-D",
            CHAIN_NAME,
            "-m",
            "set",
            "--match-set",
            SET_NAME_IPV6,
            "src",
            "-j",
            "DROP",
            ignore_error=True,
        )
        run_cmd("ipset", "destroy", SET_NAME_IPV4, ignore_error=True)
        run_cmd("ipset", "destroy", SET_NAME_IPV6, ignore_error=True)

    def test_table_rule_set_are_created(self):
        sleep(3)

        # IPV4 Chain
        output = run_cmd("iptables", "-L", CHAIN_NAME)
        rules = [line for line in output.split("\n") if SET_NAME_IPV4 in line]

        self.assertEqual(len(rules), 1)
        assert f"match-set {SET_NAME_IPV4} src" in rules[0]

        # IPV6 Chain
        output = run_cmd("ip6tables", "-L", CHAIN_NAME)
        rules = [line for line in output.split("\n") if SET_NAME_IPV6 in line]

        self.assertEqual(len(rules), 1)
        assert f"match-set {SET_NAME_IPV6} src" in rules[0]

        output = run_cmd("ipset", "list")

        assert SET_NAME_IPV6 in output
        assert SET_NAME_IPV4 in output

    def test_duplicate_decisions_across_decision_stream(self):
        d1, d2, d3 = generate_n_decisions(3, dup_count=1)
        self.lapi.ds.insert_decisions([d1])
        sleep(3)
        res = get_set_elements(SET_NAME_IPV4)
        self.assertEqual(res, {"0.0.0.0"})

        self.lapi.ds.insert_decisions([d2, d3])
        sleep(3)
        assert self.fb.poll() is None
        self.assertEqual(get_set_elements(SET_NAME_IPV4), {"0.0.0.0", "0.0.0.1"})

        self.lapi.ds.delete_decision_by_id(d1["id"])
        self.lapi.ds.delete_decision_by_id(d2["id"])
        sleep(3)
        self.assertEqual(get_set_elements(SET_NAME_IPV4), set())
        assert self.fb.poll() is None

        self.lapi.ds.delete_decision_by_id(d3["id"])
        sleep(3)
        self.assertEqual(get_set_elements(SET_NAME_IPV6), set())
        assert self.fb.poll() is None

    def test_decision_insertion_deletion_ipv4(self):
        total_decisions, duplicate_decisions = 100, 23
        decisions = generate_n_decisions(total_decisions, dup_count=duplicate_decisions)
        self.lapi.ds.insert_decisions(decisions)
        sleep(3)  # let the bouncer insert the decisions

        set_elements = get_set_elements(SET_NAME_IPV4)
        self.assertEqual(len(set_elements), total_decisions - duplicate_decisions)
        self.assertEqual({i["value"] for i in decisions}, set_elements)
        self.assertIn("0.0.0.0", set_elements)

        self.lapi.ds.delete_decisions_by_ip("0.0.0.0")
        sleep(3)

        set_elements = get_set_elements(SET_NAME_IPV4)
        self.assertEqual({i["value"] for i in decisions if i["value"] != "0.0.0.0"}, set_elements)
        self.assertEqual(len(set_elements), total_decisions - duplicate_decisions - 1)
        self.assertNotIn("0.0.0.0", set_elements)

    def test_decision_insertion_deletion_ipv6(self):
        total_decisions, duplicate_decisions = 100, 23
        decisions = generate_n_decisions(total_decisions, dup_count=duplicate_decisions, ipv4=False)
        self.lapi.ds.insert_decisions(decisions)
        sleep(3)

        set_elements = get_set_elements(SET_NAME_IPV6)
        set_elements = set(map(ip_address, set_elements))
        self.assertEqual(len(set_elements), total_decisions - duplicate_decisions)
        self.assertEqual({ip_address(i["value"]) for i in decisions}, set_elements)
        self.assertIn(ip_address("::1:0:3"), set_elements)

        self.lapi.ds.delete_decisions_by_ip("::1:0:3")
        sleep(3)

        set_elements = get_set_elements(SET_NAME_IPV6)
        set_elements = set(map(ip_address, set_elements))
        self.assertEqual(len(set_elements), total_decisions - duplicate_decisions - 1)
        self.assertEqual(
            {
                ip_address(i["value"])
                for i in decisions
                if ip_address(i["value"]) != ip_address("::1:0:3")
            },
            set_elements,
        )
        self.assertNotIn(ip_address("::1:0:3"), set_elements)

    def test_longest_decision_insertion(self):
        decisions = [
            {
                "value": "123.45.67.12",
                "scope": "ip",
                "type": "ban",
                "origin": "script",
                "duration": f"{i}h",
                "reason": "for testing",
            }
            for i in range(1, 201)
        ]
        self.lapi.ds.insert_decisions(decisions)
        sleep(3)
        elems = get_set_elements(SET_NAME_IPV4, with_timeout=True)
        self.assertEqual(len(elems), 1)
        elems = list(elems)
        self.assertEqual(elems[0][0], "123.45.67.12")
        self.assertLessEqual(abs(elems[0][1] - 200 * 60 * 60), 15)


def get_set_elements(set_name, with_timeout=False):
    output = run_cmd("ipset", "list", "-o", "xml")
    root = ET.fromstring(output)
    elements = set()
    for member in root.findall(f"ipset[@name='{set_name}']/members/member"):
        if with_timeout:
            to_add = (member.find("elem").text, int(member.find("timeout").text))
        else:
            to_add = member.find("elem").text
        elements.add(to_add)
    return elements
