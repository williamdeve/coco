Coco
----

## 简易跳板机

    基于pexpect实现的简易跳板机


## 依赖

    * python 3.6.1

    * virtualenv 默认为python3对应的版本

        # ll /usr/bin/virtualenv
        lrwxrwxrwx 1 root root 33 Dec  8 18:09 /usr/bin/virtualenv -> /usr/local/python3/bin/virtualenv


## 安装

    ➜  ~ cd /opt
    ➜  opt git clone https://github.com/yyjinlong/coco.git
    ➜  opt cd coco
    ➜  coco git:(master) ✗ python tools/install_venv.py
    ➜  coco git:(master) ✗ tools/with_venv.sh pip install git+git://github.com/yyjinlong/pexpect.git#egg=pexpect
    ➜  coco git:(master) ✗ tools/with_venv.sh python setup.py develop

    # NOTE(拷贝启动脚本)
    ➜  coco git:(master) ✗ cp coco.sh /etc/profile.d/


## 测试

     ➜  coco git:(master) ✗ tools/with_venv.sh coco-bastion --config-file=etc/development.conf
