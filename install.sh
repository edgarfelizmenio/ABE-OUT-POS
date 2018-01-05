#! /bin/bash -x

apt-get -y -q upgrade
apt-get -y -q install build-essential
apt-get -y -q install git
apt-get -y -q install vim

apt-get install -y -q lzip
apt-get install -y -q flex bison
apt-get install -y -q python3-setuptools
apt-get install -y -q python3-dev
apt-get install -y -q python3.4-venv

cd ../ABE-OUT-POS

# Install GMP
tar --lzip -xvf gmp-6.1.2.tar.lz;
cd gmp-6.1.2;
./configure;
make;
make check;
make install; # sudo make install

# Install PBC from source
cd ..
tar -xvf pbc-0.5.14.tar.gz
cd pbc-0.5.14
./configure
./configure LDFLAGS="-lgmp"
make
make install
ldconfig

# Install OpenSSL

cd ..
tar -xvf openssl-1.1.0g.tar.gz
cd openssl-1.1.0g
./config
make
make test
make install
ldconfig

# Now we can build and install Charm:
cd ..
python3 -m venv env
source env/bin/activate
pip3 install --upgrade setuptools

cd charm
./configure.sh
make install
make test

cd ..
# pip3 install -r requirements.txt

python3 sample1.py
python3 sample2.py

pip3 install -r requirements.txt

pip3 install gevent
pip3 install grequests

pip3 freeze

# install gunicorn
# pip3 install gunicorn

# install and enable nginx
# cp nginx/source-shr /etc/nginx/sites-available/source-shr
# ln -s /etc/nginx/sites-available/source-shr /etc/nginx/sites-enabled/source-shr
# sudo service nginx restart

# start the mediator
# cp upstart/source-shr.conf /etc/init/source-shr.conf
# sudo service source-shr start