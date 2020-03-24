#!/bin/bash
### check if the proces is running ###
basePath=$(cd `dirname $0`; pwd)
fullPathProc=$basePath/${0##*/}
# Run the proces by fullname
if [ $fullPathProc != $0 ]; then
  /bin/bash $fullPathProc
  exit 1
fi
pCount=$(ps -ef | grep $fullPathProc | grep -v 'grep' | grep -v ' -c sh' | grep -v $$ | grep -c 'sh')
if [ $pCount -gt 0 ]; then
  date
  echo "$fullPathProc is running, so exit now."
  exit 0
fi
echo "$fullPathProc is starting now ..."
######################################

GUNICORNPATH=$(which gunicorn)
if [ $(echo $GUNICORNPATH|wc -c) -gt 8 ]; then
  sudo ${GUNICORNPATH} --worker-class eventlet -w 1 app:app -b 0.0.0.0:5000
else
  echo 'gunicorn not found'
fi
# --worker-class eventlet -w 1 app:app -b 0.0.0.0:5000
