#!/bin/bash
echo "Running post-deploy script"


#raw sol logs saved in WORKSPACE/build-deps
#this script convert them into html by ansi2html tool
#and move them to 'build' folder for publishing
cd $WORKSPACE/build-deps
for file in `ls *sol.log.raw`; do
    # decode to utf-8 before, because ansi2html will broke when finding invalid char
    iconv -f "windows-1252" -t "UTF-8" $file -o new_$file
    ansi2html < new_$file > $WORKSPACE/build-deps/${file%.*}
done
