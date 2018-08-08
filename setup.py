# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

import setuptools

with open("README", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hinawa-utils",
    version="0.0.99",
    author="Takashi Sakamoto",
    author_email="o-takashi@sakamocchi.jp",
    description="Utility to control Audio and Music units on IEEE 1394 bus",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/takaswie/hinawa-utils",
    classifiers=(
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Development Status :: 4 - Beta",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "Intended Audience :: Developers",
        "Environment :: Console",
    ),
    packages=(
        'hinawa_utils',
        'hinawa_utils.bebob',
        'hinawa_utils.dg00x',
        'hinawa_utils.dice',
        'hinawa_utils.efw',
        'hinawa_utils.ieee1212',
        'hinawa_utils.ieee1394',
        'hinawa_utils.misc',
        'hinawa_utils.motu',
        'hinawa_utils.oxfw',
        'hinawa_utils.ta1394',
        'hinawa_utils.tscm',
    ),
    scripts=(
        'hinawa-bebob-parser',
        'hinawa-config-rom-printer',
        'hinawa-dg00x-cui',
        'hinawa-dice-common-cui',
        'hinawa-dice-extension-cui',
        'hinawa-fireworks-cui',
        'hinawa-focusrite-saffirepro-io-cui',
        'hinawa-griffin-firewave-cui',
        'hinawa-lacie-speakers-cui',
        'hinawa-maudio-bebob-cui',
        'hinawa-motu-common-cui',
        'hinawa-oxfw-generic-cui',
        'hinawa-tascam-fireone-cui',
        'hinawa-tascam-fw-console-cui',
        'hinawa-tascam-fw-rack-cui',
        'hinawa-yamaha-terratec-cui',
    ),
)
