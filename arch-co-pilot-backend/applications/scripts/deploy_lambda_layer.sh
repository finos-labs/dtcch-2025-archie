#!/usr/bin/env bash


while [[ "$#" -gt 0 ]]; do case $1 in
  -v|--version) pythonEnvs+=("$2"); shift;;
  -n|--layer-name) layerName="$2"; shift;;
  -d|--desc) layerDescription="$2"; shift;;
  -e|--env) deploymentEnv="$2"; shift;;
  -r|--region) Region="$2"; shift;;
  *) echo "Unknown parameter passed: $1"; exit 1;;
esac; shift; done

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo "Script directory: $SCRIPT_DIR"


rm -rf ../layers/${layerName} && mkdir -p ../layers/${layerName}
cd ../layers/${layerName}
cp ../requirements.txt ./

more requirements.txt
sudo rm -rf python && mkdir -p python
echo "in directory `pwd`"
# Create and install requirements to directory.


for penv in ${pythonEnvs[@]}; do
    mkdir -pv python
    docker run -v "$PWD":/var/task "public.ecr.aws/sam/build-python${penv}" /bin/sh -c "pip install -q -r requirements.txt -t python/; exit"
done

echo "aws lambda list-layer-versions --layer-name ${layerName}-${deploymentEnv}"
layer_version=$(aws lambda list-layer-versions --layer-name ${layerName}-${deploymentEnv}| jq -r '.[] | .[] | .Version')
curr_layer_version=${layer_version}
layer_version=$((layer_version+1))
echo "layer_version for  ${layerName} is ${layer_version}"

#Create zip file of environments.
zip -r ${layerName}-${layer_version}.zip python


if [[ $deploymentEnv == *"dev"* ]]; then
    Env="devx"
else
    Env="prod"
fi

deploy_package=false

# shellcheck disable=SC1020
if [[ $curr_layer_version != '' ]]; then
  aws s3 cp s3://archi-deploy-platform-bucket-${Env}lambda/layers/${layerName}/${deploymentEnv}/${layerName}-${curr_layer_version}.zip ./ --profile archi

  echo "layer_version for  ${layerName} is ${layer_version}; curr_layer_version is ${curr_layer_version}"

  curr_prev_diff=$(diff \
  <(unzip -vqq ${layerName}-${curr_layer_version}.zip  | awk '{$2=""; $3=""; $4=""; $5=""; $6=""; print}' | sort -k3 -f) \
  <(unzip -vqq ${layerName}-${layer_version}.zip  | awk '{$2=""; $3=""; $4=""; $5=""; $6=""; print}' | sort -k3 -f))

  if [[ $curr_prev_diff != '' ]]; then
    #copy package to S3
    aws s3 cp ./${layerName}-${layer_version}.zip s3://archi-deploy-platform-bucket-${Env}/lambda/layers/${layerName}/${deploymentEnv}/
    deploy_package=true
  fi
  #rm -rf ./${layerName}-${curr_layer_version}.zip
else
  aws s3 cp ./${layerName}-${layer_version}.zip s3://archi-deploy-platform-bucket-${Env}/lambda/layers/${layerName}/${deploymentEnv}/
  deploy_package=true
fi

