# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hinawa-utils",
    version="0.3.0",
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
        'hinawa_utils.fireface',
        'hinawa_utils.ieee1212',
        'hinawa_utils.ieee1394',
        'hinawa_utils.misc',
        'hinawa_utils.motu',
        'hinawa_utils.oxfw',
        'hinawa_utils.ta1394',
        'hinawa_utils.tscm',
    ),
    scripts=(
        'hinawa-alesis-io-cli',
        'hinawa-apogee-ensemble-cli',
        'hinawa-apogee-duet-cli',
        'hinawa-bebob-plug-parser',
        'hinawa-bebob-connection-cli',
        'hinawa-config-rom-printer',
        'hinawa-dg003-cli',
        'hinawa-dg00x-common-cli',
        'hinawa-dice-common-cli',
        'hinawa-dice-extension-cli',
        'hinawa-edirol-fa-cli',
        'hinawa-fireface-cli',
        'hinawa-fireworks-cli',
        'hinawa-focusrite-saffirepro-io-cli',
        'hinawa-griffin-firewave-cli',
        'hinawa-lacie-speakers-cli',
        'hinawa-maudio-bebob-cli',
        'hinawa-motu-common-cli',
        'hinawa-oxfw-generic-cli',
        'hinawa-tascam-fireone-cli',
        'hinawa-tascam-fw-console-cli',
        'hinawa-tascam-fw-rack-cli',
        'hinawa-yamaha-terratec-cli',
    ),
)
