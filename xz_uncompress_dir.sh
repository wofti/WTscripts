#!/bin/sh
dir=$1
# recreate directory from archive
# sbatch -p shortq7 ./<this script>
if [ -e "${dir%/}.txz" ]; then
  echo "uncompressing archive: ${dir%/}.txz"
  time tar xf ${dir%/}.txz
else
  echo "no archive: ${dir%/}.txz"
fi
