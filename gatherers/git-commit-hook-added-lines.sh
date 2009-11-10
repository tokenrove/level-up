#!/bin/sh

host=`hostname`
directory=`pwd`
code='9IOKVgiIZOM='
metric="git commit $host:$directory"
unit="lines of code"
url="http://localhost:8080/metric"
#url="https://level-up.appspot.com/metric"


count=`git show -1 HEAD | grep '^\+' | wc -l`
curl -F 'code='"$code" \
     -F 'metric='"$metric" \
     -F "value=$count" -F "unit=$unit" $url
