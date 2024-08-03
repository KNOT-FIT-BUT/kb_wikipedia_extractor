#!/bin/bash
# Author: Tomas Volf, ivolf@fit.vutbr.cz
# Contributor: Jan Kapsa, xkapsa00@fit.vutbr.cz

# TODO: -g, -p, -r processing

export LC_ALL="C.UTF-8"

# default values
SAVE_PARAMS=$*
LOG=false
LANG=en
DUMP_PATH=/mnt/minerva1/nlp/corpora/monolingual/english/wikipedia/
DUMP_VERSION=latest
DEBUG_LIMIT=10000

# saved values
LAUNCHED=`readlink -f "$0"`

NPROC=`nproc`
GB_THRESHOLD=10
FREE_MEMORY=$((`awk '/MemAvailable/ { printf "%.0f \n", $2/1024/1024 }' /proc/meminfo`))
NPROC=$((FREE_MEMORY / NPROC >= GB_THRESHOLD ? NPROC : FREE_MEMORY / GB_THRESHOLD))

#=====================================================================
# nastavovani parametru prikazove radky

usage()
{
    DUMP_PATH="${DUMP_PATH})"
    cut_DUMP_PATH=$((`tput cols` - 25))
    echo "Usage: start.sh [PARAMETERS]"
    echo ""
    echo -e "  -h, --help   show this help message and exit"
    echo ""
    echo -e "OPTIONAL arguments:"
    echo -e "  -l <lang>    language of wikipedia dumps to process (default: ${LANG})"
    echo -e "  -m <int>     number of pool processes to parallelize entities processing (default: ${NPROC})"
    echo -e "  -d <version> version of dumps to process (default: ${DUMP_VERSION})"
    echo -e "  -I <path>    set a dir path of wikipedia dump files serving as input for KB creation purposes"
    echo -e "               (default: ${DUMP_PATH::${cut_DUMP_PATH}}"
    if test $cut_DUMP_PATH -lt ${#DUMP_PATH}
    then
        echo -e "               ${DUMP_PATH:${cut_DUMP_PATH}}"
    fi
    echo -e "  --debug [<int>]  Number of pages to process in debug mode (default: 10.000)"
    echo -e "  -u [<login>] upload (deploy) KB to webstorage via given login"
    echo -e "               (default current user)"
    echo -e "  --dev        Development mode (upload to separate space to prevent forming a new production/stable version of KB)"
    echo -e "  --test       Test mode (upload to separate space to prevent forming a new production/stable version of KB)"
    echo -e "  --log        log to start.sh.stdout, start.sh.stderr and start.sh.stdmix"
    echo ""
#    echo -e "MULTIPLE DUMP PATHS CUSTOMIZATION:"
#    echo -e "  -g <path>    set a path of wikipedia geo tags dump file input"
    echo -e "  -p <path>    set a path of Wikipedia pages dump file input"
#    echo -e "  -r <path>    set a path of wikipedia redirects dump file input"
    echo -e "  --skip-redirects  Skip processing of redirects"
    echo ""
}

CUSTOM_DUMP_PATH=false
CUSTOM_REDIR_PATH=false
DEBUG_LIMIT_USED=false
SKIP_REDIRECTS=false
PAGES_PATH=
REDIR_PATH=
SENTENCE_PATH=
DEPLOY=false
MULTIPROC_PARAMS="-m ${NPROC}"
EXTRACTION_ARGS=()
KB_STABILITY=

while [ "$1" != "" ]; do
    PARAM=`echo $1 | awk -F= '{print $1}'`
    VALUE=`echo $1 | awk -F= '{print $2}'`
    case $PARAM in
        -h | --help)
            usage
            exit
            ;;
        -d)
            DUMP_VERSION=$2
            shift
            ;;
        -I)
            CUSTOM_DUMP_PATH=true
            DUMP_PATH=$2
            shift
            ;;
        -l)
            LANG=$2
            shift
            ;;
        -p)
            PAGES_PATH=$2
            shift
            ;;
#        -r)
#            CUSTOM_REDIR_PATH=true
#            REDIR_PATH=$2
#            shift
#            ;;
        -m)
            MULTIPROC_PARAMS="-m ${2}"
            shift
            ;;
        -u)
            DEPLOY=true
            LOGIN=$2
            if test "${LOGIN:0:1}" = "-"
            then
                DEPLOY_USER=`whoami`
            else
                DEPLOY_USER=$2
                shift
            fi
            ;;
        --debug)
            DEBUG_LIMIT_USED=true
            VALUE=$2
            if test "${VALUE:0:1}" != "-"
            then
               DEBUG_LIMIT=$VALUE
               shift
            fi
            ;;
        --skip-redirects)
            SKIP_REDIRECTS=true
            ;;
        --dev)
            KB_STABILITY="--dev"
            ;;
        --test)
            if test -z "${KB_STABILITY}"
            then
              KB_STABILITY="--test"
            fi
            ;;
        --log) LOG=true
            ;;
        *)
            >&2 echo "ERROR: unknown parameter \"$PARAM\""
            usage
            exit 1
            ;;
    esac
    shift
done

# zmena spousteci cesty na tu, ve ktere se nachazi start.sh
cd `dirname "${LAUNCHED}"`

if $LOG; then
	rm -f start.sh.fifo.stdout start.sh.fifo.stderr start.sh.fifo.stdmix
	mkfifo start.sh.fifo.stdout start.sh.fifo.stderr start.sh.fifo.stdmix

	cat start.sh.fifo.stdout | tee start.sh.stdout > start.sh.fifo.stdmix &
	cat start.sh.fifo.stderr | tee start.sh.stderr > start.sh.fifo.stdmix &
	cat start.sh.fifo.stdmix > start.sh.stdmix &
	exec > start.sh.fifo.stdout 2> start.sh.fifo.stderr
fi

# reading the config file
use_config=false
while read -r line; do
    # Reading each line 
    if [[ -n $line ]];
    then
        if [[ ${line:0:1} != "#" ]]; 
        then 
            IFS='=' read -ra ADDR <<< "$line"
            for i in "${ADDR[@]}"; do
                case $i in
                USE_CONFIG)
                    if [ ${ADDR[i+1]} = "TRUE" ] 
                    then
                        echo "using config file"
                        use_config=true
                    fi
                    break
                    ;;
                LANG)
                    if [ "$use_config" = true ] 
                    then
                        # echo ${ADDR[i+1]}
                        LANG=${ADDR[i+1]}
                    fi
                    break
                    ;;
                IN_DIR)
                    if [ "$use_config" = true ] 
                    then
                        # echo ${ADDR[i+1]}
                        CUSTOM_DUMP_PATH=true
                        DUMP_PATH=${ADDR[i+1]}
                    fi
                    break
                    ;;
                DUMP)
                    if [ "$use_config" = true ] 
                    then
                        # echo ${ADDR[i+1]}
                        DUMP_VERSION=${ADDR[i+1]}
                    fi
                    break
                    ;;
                PROCESSES)
                    if [ "$use_config" = true ] 
                    then
                        # echo ${ADDR[i+1]}
                        NPROC=${ADDR[i+1]}
                        MULTIPROC_PARAMS="-m ${NPROC}"
                    fi
                    break
                    ;;
                SENTENCES)
                    if [ "$use_config" = true ] 
                    then
                        # echo ${ADDR[i+1]}
                        SENTENCE_PATH=${ADDR[i+1]}
                    fi
                    break
                    ;;
                *)
                    echo "Invalid config argument"
                    ;;
                esac
            done
        fi
    fi
done < kb.config

DUMP_DIR=`dirname "${DUMP_PATH}"`

# If Wikipedia dump path is symlink, then read real path
get_real_path() {
    TMP_PATH=${1}
    REQUIRED_DIR=${2}

    if test -z "${REQUIRED_DIR}"
    then
        REQUIRED_DIR=`dirname "${LAUNCHED}"`
    fi

    if test -L "${TMP_PATH}"
    then
        TMP_PATH=`readlink -f "${TMP_PATH}"`
    fi
    if test `dirname "${TMP_PATH}"` = "."
    then
        TMP_PATH="${REQUIRED_DIR}/${TMP_PATH}"
    fi

    echo "${TMP_PATH}"
}

DUMP_PATH=`get_real_path "${DUMP_PATH}" "${DUMP_DIR}"`
if test "${PAGES_PATH}" != ""
then
    PAGES_PATH=`get_real_path "${PAGES_PATH}"`
fi

# Test file existence and zero-length of file
#if test ! -s "${DUMP_PATH}" -o ! -r "${DUMP_PATH}"
#then
#    >&2 echo "ERROR: wikipedia pages dump file does not exist or is zero-length"
#    exit 2
#fi

# If custom redirects path was not set, extract the default one
#if ! ${CUSTOM_REDIR_PATH}
#then
#    REDIR_PATH="`dirname "${DUMP_PATH}"`/redirects_from_`basename "${DUMP_PATH}"`"
#fi

# Extract Wikipedia dump file version number
#VERSION=`basename "${DUMP_PATH}" | sed 's/^.*\([0-9]\{8\}\).*$/\1/'`
#if test ${#VERSION} -ne 8
#then
#    >&2 echo "ERROR: can not parse version info from path - name of input file must contain 8-digit (date) version info"
#    exit 3
#fi

EXTRACTION_ARGS+=(${KB_STABILITY})
EXTRACTION_ARGS+=(${MULTIPROC_PARAMS})
if [ -n "$SENTENCE_PATH" ]; then
    EXTRACTION_ARGS+=("-s ${SENTENCE_PATH}")
fi

if test "${DEBUG_LIMIT_USED}" = true
then
    EXTRACTION_ARGS+=("--debug ${DEBUG_LIMIT}")
fi

if test "${PAGES_PATH}" != ""
then
    EXTRACTION_ARGS+=("-p ${PAGES_PATH}")
fi

if test "${SKIP_REDIRECTS}" = true
then
     EXTRACTION_ARGS+=("-r \"\"")
fi

# Run CS Wikipedia extractor to create new KB
# old code:
# CMD="python3 wiki_cs_extract.py --lang ${LANG} --dump ${DUMP_VERSION} --indir \"${DUMP_PATH}\" ${EXTRACTION_ARGS[@]} 2>entities_processing.log"

# if [ $LANG == "en" ]; then
#     echo "GENERATING: langmap.json"
#     CMD="python3 generate_langmap.py"
#     eval $CMD
# fi

mkdir -p outputs
CMD="python3 wiki_extract.py --lang ${LANG} --dump ${DUMP_VERSION} --indir \"${DUMP_PATH}\" ${EXTRACTION_ARGS[@]} 2>outputs/kb.out"
echo "RUNNING COMMAND: ${CMD}"
eval $CMD

retVal=$?
if [ $retVal -ne 0 ]; then
    echo ""
    echo "Error while running python script"
    exit $retVal
fi

# Add metrics to newly created KB
if $LOG
then
    metrics_params="--log"
fi

./metrics/start.sh ${metrics_params}
retVal=$?
if [ $retVal -ne 0 ]; then
    echo ""
    echo "Error while running metrics script (error code: ${retVal})."
    exit $retVal
fi

# Convert Wikipedia KB format to Generic KB format
python3 kbwiki2gkb.py --indir outputs --outdir outputs
retVal=$?
if [ $retVal -ne 0 ]; then
    echo ""
    echo "Error while running kbwiki2gkb script (error code: $retVal)."
    exit $retVal
fi

if $DEPLOY
then
    ./deploy.sh -u $DEPLOY_USER
fi
