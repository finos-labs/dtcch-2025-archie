#!/usr/bin/env bash


while [[ "$#" -gt 0 ]]; do case $1 in
  -s|--src) srcDir="$2"; shift;;
  -n|--name) functionName="$2"; shift;;
  -e|--env) deploymentEnv="$2"; shift;;
  *) echo "Unknown parameter passed: $1"; exit 1;;
esac; shift; done
function_dir=$(echo "${srcDir}" | tr '-' '_')
echo "function_dir --> ${function_dir}"

echo "in directory0 `pwd`"
cd ..
mkdir ${functionName}
cp  ./${function_dir}/src/* ./${functionName}/
cp -rf ./common ./${functionName}/
cp ./${function_dir}/config.yaml ./${functionName}/
cd ./${functionName}/
echo "in directory `pwd`"
rm -f ${functionName}.zip
zip_ts=$(date +%s)
# Create zip file of environments.
zip_cmnd="zip -r ${functionName}_${zip_ts}.zip . -x '*/__pycache__' '*/__pycache__/*' '*/.git/*'"
eval $zip_cmnd

export lambda_name="${functionName}_${zip_ts}.zip"

if [[ $deploymentEnv == *"dev"* ]]; then
    Env="dev"
else
    Env="prod"
fi
echo "env = ${Env}"
# copy package to S3
echo "running --> aws s3 cp ./${functionName}_${zip_ts}.zip s3://archi-deploy-platform-bucket-devx/lambda/functions/${functionName}/${deploymentEnv}/"
aws s3 cp ./${functionName}_${zip_ts}.zip s3://archi-deploy-platform-bucket-devx/lambda/functions/${functionName}/${deploymentEnv}/

