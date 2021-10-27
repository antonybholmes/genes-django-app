pwd=`pwd`
name=`basename ${pwd}`
echo ${name}
docker container ls -a | grep ${name} | cut -f1 -d' ' | xargs docker container rm -f
