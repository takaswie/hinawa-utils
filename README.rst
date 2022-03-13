============
hinawa-utils
============

2022/03/13
Takashi Sakamoto

Disclaimer
==========

This project is under maintenance mode. It's probable just to fix minor issues
when reported, while any integration for new features is not planned.

As an alternative, `snd-firewire-ctl-services <https://github.com/alsa-project/snd-firewire-ctl-services>`_ project
is available with more integrated framework. Users are expected to migrate to it.

Introduction
============

This batch of Python 3 codes consists of modules and scripts to control
Audio and Music units on IEEE 1394 bus, with a help of PyGObject for
gobject-introspection to libhinawa APIs.

The modules include applications of below specifications:

* IEEE 1212:2001 - IEEE Standard for a Control and Status Registers (CSR)
  Architecture for Microcomputer Buses
* IEEE 1394:2008 - IEEE Standard for a High-Performance Serial Bus
* AV/C Digital Interface Command Set General Specification Version 4.2
  (Sep. 2004, 1394 Trade Association)
* AV/C Audio Subunit Specification 1.0 (Oct. 2000, 1394 Trade Association)
* AV/C Connection and Compatibility Management Specification 1.1
  (Mar. 2003, 1394 Trade Association)
* Configuration ROM for AV/C Devices 1.0 (Dec. 2000, 1394 Trade Association)
* AV/C Stream Format Information Specification 1.1 - Working draft
  revision 0.5 (Apr. 2005, 1394 Trade Association)
* Vendor specific protocols:
   * Some protocols for BridgeCo Enhanced Break Out Box (BeBoB) of
     BridgeCo AG.
   * General and extended protocol for Digital Interface Communication
     Engine (DICE) of TC Applied Technologies and ASICs of DiceII,
     TCD2210 (Dice Mini), TCD2220 (Dice Jr.).
   * Protocol for Fireworks board module of Echo Audio corporation.
   * Protocol for Digi 00x series of Digidesign.
   * Protocol for FireWire series of TEAC (TASCAM).
   * Common protocol for each generation of FireWire series of Mark of
     the Unicorn (MOTU).
   * Protofol for Fireface series of RME GmbH.
   * Some protocols specific to manufacturer.

CLI tools to control Audio and Music unit on IEEE 1394 bus
==========================================================

* hinawa-config-rom-printer
   * A lexer/parser of configuration ROM on IEEE 1394 bus
* hinawa-bebob-plug-parser
   * Plug structure parser for BeBoB firmware
* hinawa-bebob-connection-cli
   * Signal connection management between plugs of subunits for BeBoB firmware
* hinawa-alesis-io-cli
   * CLI tool for Alesis iO|14 and iO|26
* hinawa-apogee-duet-cli
   * CLI tool for Apogee Duet FireWire
* hinawa-apogee-ensemble-cli
   * CLI tool for Apogee Ensemble
* hinawa-dg00x-common-cli
   * CLI tool for common functionalities of Digidesign Digi 00x family
* hinawa-dg003-cli
   * CLI tool for functionalities specific to Digidesign Digi 003 family
* hinawa-dice-common-cli
   * CLI tool for Dice common functionalities
* hinawa-dice-extension-cli
   * CLI tool for Dice extended functionalities
* hinawa-fireface-cli
   * CLI tool for RME Fireface series
* hinawa-fireworks-cli
   * CLI tool for Echo Audio Fireworks module
* hinawa-griffin-firewave-cli
   * CLI tool for Griffin Firewave
* hinawa-lacie-speakers-cli
   * CLI tool for Lacie FireWire speakers
* hinawa-motu-common-cli
   * CLI tool for MOTU FireWire series
* hinawa-maudio-bebob-cli
   * CLI tool for M-Audio FireWire series based on BeBoB solution
* hinawa-oxfw-generic-cli
   * CLI tool for OXFW generic functionalities
* hinawa-tascam-fireone-cli
   * CLI tool for Tascam FireOne
* hinawa-tascam-fw-rack-cli
   * CLI tool for rack models of Tascam FireWire series (FW1804)
* hinawa-tascam-fw-console-cli
   * CLI tool for console models of Tascam FireWire series (FW1082/1884)
* hinawa-yamaha-terratec-cli
   * CLI tool for Yamaha GO series and Terratec PHASE series
* hinawa-focusrite-saffirepro-io-cli
   * CLI tool for Focusrite SaffirePro IO series

Requirements
============

* Python 3.4 or later
   * https://docs.python.org/3/library/enum.html
   * https://docs.python.org/3/library/pathlib.html
* PyGObject
   * https://gitlab.gnome.org/GNOME/pygobject
* libhinawa 2.0.0 or later, with gir support
   * https://github.com/takaswie/libhinawa

License
=======

* All modules are licensed under GNU Lesser General Public License version 3 or
  later.
* All scripts are licensed under GNU General Public License version 3 or later.

End
