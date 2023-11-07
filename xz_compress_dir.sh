#!/bin/sh
dir=$1
# move dir to highly compressed archive
# do not use if directory is <32M (use default XZ_OPT instead)
# compression time can take up to 1h per 3G
# for <20G use 6h partition: sbatch -p shortq7 ./<this script>
# for >20G use 3d partition: sbatch -p mediumq7 ./<this script>
if [ -e "${dir%/}.txz" ]; then
  echo "already exists: ${dir%/}.txz"
else
  if [ -d "${dir%/}" ]; then
    echo "moving files to compressed archive: ${dir%/}.txz"
    time XZ_OPT=-9 tar cJf ${dir%/}.txz ${dir%/} --remove-files
  else
    echo "no directory: ${dir%/}"
  fi
fi
