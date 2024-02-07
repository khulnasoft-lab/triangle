#!/usr/bin/env python3
# Copyright salsa-ci-team and others
# SPDX-License-Identifier: FSFAP
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved. This file is offered as-is, without any warranty.

import sys
import logging
import argparse
from junit_xml import TestSuite, TestCase


def main(filename, ignore_warnings=False):
    test_cases = []
    with open(filename) as fh:
        for line in fh:
            line_split = line.split(':', 2)
            if len(line_split) < 3:
                continue
            level, package, message = [x.strip() for x in line_split]
            test_case = TestCase(package)
            if level == 'E' or (not ignore_warnings and level == 'W'):
                test_case.add_failure_info(message)
            test_cases.append(test_case)
    ts = TestSuite("Lintian2Junit", test_cases)
    return TestSuite.to_xml_string([ts])


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.DEBUG,
                        stream=sys.stdout)
    parser = argparse.ArgumentParser(description='Lintian to junit')
    parser.add_argument('--ignore-warnings',
                        help='Only consider errors, warnings will be ignored',
                        action='store_true')
    parser.add_argument(
        '-l', '--lintian-file',
        type=str,
        help='Lintian output to be parsed',
        required=True,
    )
    args = parser.parse_args()
    junit_xml = main(args.lintian_file, args.ignore_warnings)
    print(junit_xml)
