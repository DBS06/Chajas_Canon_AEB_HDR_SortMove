#!/usr/bin/python

import sys
import os
import argparse


def main():  # pragma: no cover
    """
    parsing commandline args
    """

    parser = create_parser()
    args = parser.parse_args()

    print(args.path)
    if args.quiet:
        print("quiet")
    else:
        print("loud")


def create_parser():  # pragma: no cover
    """
    sets up the main commandline parser

    :return: parser object
    """
    main_parser = argparse.ArgumentParser(
        description='This script helps to sort HDR images from Canon Cameras')

    main_parser.add_argument("-p", "--path", action="store", default='', help="path to image folder")
    main_parser.add_argument("-q", "--quiet", action="store_true", default='', help="Dont ask if sorting should start")

    # add_argument_completion(main_parser, "--docker", action="store_true", help="run stuff in docker container")
    # # add_argument_completion(main_parser,"--docker", action="store_true", help="run stuff in docker container")
    # add_argument_completion(main_parser, "--docker-cfg", dest='docker_config_file', nargs="?",
    #                         default='scripts/.docker.json', action="store",
    #                         help="config file for docker environment (default: scripts/.docker.json)")

    # add_argument_completion(main_parser, "--ng-master-app-path", action="store", nargs="?", default='/fw/ng-master-app',
    #                         help="location of the ng-master-app repository")

    # add_argument_completion(main_parser, "--docker-image", action="store", nargs="?",
    #                         help="docker image (overwrites values in config file)")

    # add_argument_completion(main_parser, "--docker-image-tag", action="store", nargs="?",
    #                         help="docker image (overwrites values in config file)")

    # add_argument_completion(main_parser, "--keep-container", action="store_true",
    #                         help="do not delete the container after execution (only for debuging purposes)")

    # subparser = main_parser.add_subparsers(help="sub commands", dest="subcmd")

    return main_parser


if __name__ == "__main__":  # pragma: no cover
    main()
    sys.exit(0)
