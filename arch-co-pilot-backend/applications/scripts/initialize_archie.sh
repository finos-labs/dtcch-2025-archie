#!/usr/bin/env bash


#copy common code to arch_copilot and arch_rag_builder application
cp -rf $HOME/arch-co-pilot/arch-co-pilot-backend/applications/common  $HOME/arch-co-pilot/arch-co-pilot-backend/applications/arch_copilot/
cp -rf $HOME/arch-co-pilot/arch-co-pilot-backend/applications/common  $HOME/arch-co-pilot/arch-co-pilot-backend/applications/arch_rag_builder/

#get ec2 region and set aws defult region to ec2 region
aws_region=`ec2-metadata -z | grep -Po "(us|sa|eu|ap)-(north|south|central)?(east|west)?-[0-9]+"`
aws configure set region $aws_region
 