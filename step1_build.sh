pwd=`pwd`
name=`basename ${pwd}`

docker build . -t ${name}
