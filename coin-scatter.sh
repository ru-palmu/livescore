#!/bin/sh
#set -e
####################################################################
#
#
#
# @author GAN
####################################################################
#declare -r version=0.1

HERE=`dirname "$0"`

usage()
{
	if [ $# -ne 0 ]
	then
		echo "$@" >& 2
	fi


	cat <<- EOF 1>&2
	Usage $0 [-h][-d directory]
	    -h: print this message
EOF
}


OPT=
DIR=$HERE/../meter/img/livescore
while getopts hd: OPT
do
	case $OPT in
	d)
		DIR=$OPTARG ;;
	h)
		usage
		exit 1;;
	\?)
		usage "invalid option"
		exit 1 ;;
	esac
done
shift `expr $OPTIND - 1`


CMD="python3 makecsv.py --x 150_000 --ymin 1.6 --ymax 3.6 --no-model --no-livescore"
for coin in 10 100 1000; do
	FILE=$DIR/${coin}coin-NNgifters.png
	$CMD --scatter $FILE --heatmap ${coin}coin --cmap turbo .
	if [ $? -ne 0 ]; then
		exit 1
	fi
	continue

	for N in `seq 1 20`; do
		rm -f $DIR/${coin}-${N}.png
		FILE=$DIR/${coin}coin-${N}gifters.png
		$CMD --scatter $FILE --dimension ${coin}coin${N} .
		break
	done
	N=21
	FILE=$DIR/${coin}coin-${N}gifters.png
	$CMD --scatter $DIR/${coin}coin-${N}gifters.png --dimension ">${coin}coin20" .
done


# EOF

