#!/bin/sh

host=`hostname`
directory=`pwd`
code=`cat ~/.level-up-code`
metric="git commit `basename $directory`"
unit="lines of code"
ratio="1:1"
#url="http://localhost:8080/metric"
url="https://level-up.appspot.com/metric"


count=`git show -1 HEAD | grep '^\+' | wc -l`
curl -F 'code='"$code" \
     -F 'metric='"$metric" \
     -F 'ratio='"$ratio" \
     -F "value=$count" -F "unit=$unit" $url
