# Hosts-Assistant

帮助更新hosts文件

由于hosts文件经常失效，手动改hosts还是挺麻烦的，所以写了这个软件。这是我学Python没多久时写的，所以代码质量可能一般般。

软件安装方法：

1、首先获得hosts文件的读写权限，最简单的方法是执行命令：sudo chmod 777 /etc/hosts 如果觉得这种方法不安全，可       以将本py文件所有者改为root，然后给本文件加上setuid标志。

2、安装python3的tkinter模块，命令： sudo apt-get install python3-tk

3、打开终端，在终端中输入命令：python3 绝对路径/Hosts助手.py （注意！一定要是绝对路径）

4、成功，以后可以从启动器打开

![](/home/ding/Desktop/深度截图_选择区域_20170714001854.png?nocache2650=1508173524464)