#!/usr/bin/env bash

#install git
sudo yum update -y
sudo yum install git -y
git — version

#install docker
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user


#install python3.12
sudo dnf install -y git tar gcc \
                   zlib-devel bzip2-devel readline-devel \
                   sqlite sqlite-devel openssl-devel \
                   tk-devel libffi-devel xz-devel

sudo curl https://pyenv.run | bash && \
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc && \
    echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc && \
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc && \
    source ~/.bashrc && \
    pyenv install 3.12.4 && \
    pyenv global 3.12.4

#get requirements file and install python dependencies
aws s3 cp s3://archi-deploy-platform-bucket-devx/scripts/requirements.txt ./
#pip3 install -r requirements.txt



yum install -y libglvnd-glx
