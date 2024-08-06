#!/bin/sh
/opt/scripts/nut_users.py
/usr/sbin/upsdrvctl start
/usr/sbin/upsd
/bin/busybox sleep 10h
/opt/scripts/mqtt.py
