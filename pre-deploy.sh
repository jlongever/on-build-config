#!/bin/bash
echo "Running pre-deploy script"

#raw sol logs saved in WORKSPACE/build-log
#this script convert them into html by ansi2html tool
#and move them to 'build-log' folder for publishing
cd $WORKSPACE/build-log
for file in `ls *sol.log.raw`; do
    ansi2html < $file > $WORKSPACE/build-log/${file%.*}
done

