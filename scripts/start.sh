#!/bin/sh
/opt/scripts/nut_users.py
/usr/sbin/upsdrvctl start
/usr/sbin/upsd
/opt/scripts/mqtt.py
