#! /bin/bash

sudo ./root-bootstrap.sh
./user-bootstrap.sh

pip install -r requirements.txt
