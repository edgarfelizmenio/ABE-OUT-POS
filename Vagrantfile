VAGRANTFILE_API_VERSION = "2"
DEFAULT_BOX = "ubuntu/trusty64"

ENV["LC_ALL"] = "en_US.UTF-8"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

    config.vm.define("ABE-OUT-POS") do |bsw_ta|
        bsw_ta.vm.box = DEFAULT_BOX
        bsw_ta.vm.provider "virtualbox" do |v|
            v.name = "ABE-OUT-POS"
            v.customize ["modifyvm", :id, "--memory", 1024]
        end

        bsw_ta.vm.network "public_network", ip: "192.168.1.103"

        bsw_ta.vm.synced_folder ".", "/home/ABE-OUT-POS",
            type: "rsync",
            rsync__exclude: ['gmp-6.1.2', 'pbc-0.5.14', 'openssl-1.1.0g', 'env', 'install']

        bsw_ta.vm.provision "update", type: :shell do |shell|
            shell.inline = "apt-get -y -q update"
        end

        bsw_ta.vm.provision "install_htop", type: :shell do |shell|
            shell.inline = "apt-get -y -q install htop"
        end

        bsw_ta.vm.provision "install", type: :shell do |shell|
            shell.path = "install.sh"
        end

    end
    
end