#!/bin/bash

VERSIONS=$(gcloud app versions list --service $1 --sort-by '~version' --format 'value(version.id)')
COUNT=0
echo "Keeping the $2 latest versions of the $1 service"
for VERSION in $VERSIONS
do
    ((COUNT++))
    if [ $COUNT -gt $2 ]
    then
      echo "Going to delete version $VERSION of the $1 service."
      gcloud app versions delete $VERSION --service $1 -q
    else
      echo "Going to keep version $VERSION of the $1 service."
    fi
done

# To delete all the app versions except last N - bash gcloud-delete.sh default N