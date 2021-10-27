pwd=`pwd`
name=`basename ${pwd}`

docker run -p 8090:8090 -d --name ${name} --network host ${name} 
