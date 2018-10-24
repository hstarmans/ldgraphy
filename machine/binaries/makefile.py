#!/usr/bin/env python3
import argparse
import glob
import os


COMPILER = 'pasm'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--make', action='store_true', help='compiles *.p to *.bin with pasm')
    parser.add_argument('--clean', action='store_true', help'removes binaries')
    return parser.parse_args()


def make():
    for file in glob.glob("*.bin"):
        os.system(f'{COMPILER} -b {file}')


def clean():
    os.system('rm -rf *.bin')
    

if __name__ == '__main__':
    args = parse_args()
    if args.make:
        make()
    if args.clean:
        clean()

