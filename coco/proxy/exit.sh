#!/bin/bash

ttid=`tty`
fuser -k $ttid
