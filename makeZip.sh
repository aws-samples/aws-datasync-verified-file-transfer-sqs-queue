#!/bin/bash

cd ./datasync_log
zip -r ../datasync_log.zip ./*
cd ../datasync_log_prep
pip install -r requirements.txt -t .
zip -r ../datasync_log_prep.zip ./*
