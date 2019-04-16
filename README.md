# P4-BIER

This repository contains the P4 based implementation of BIER(-FRR) including the distributed control plane.

* Install: Contains the installation script, which installs all required dependencies.
* Controller-Implementation: Contains the Python implementation of the global Controller.
* Local-Controller: Contains the Python implementation of the local controller. 
* P4-Implementation: Contains the data plane implementation of BIER(-FRR) in P4.
* protos: Contains the protobuf defintion for the communication between local and global controller. 

## Installation

Inside the `Install` folder, run `./setup.sh`. This will install all required dependencies. The installation process has been verified for Ubuntu 18.0.4.2 LTS.

## Usage

## Documentation

A documentation for the data plane implementation can be found in the repository wiki.

