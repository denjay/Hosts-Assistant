"""
由于hosts文件经常失效，手动改hosts还是挺麻烦的，所以写了这个软件。
这是我学Python没多久时写的，所以代码质量可能一般般。
软件安装方法：
1、首先获得hosts文件的读写权限，最简单的方法是执行命令：sudo chmod 777 /etc/hosts
   如果觉得这种方法不安全，可以将本py文件所有者改为root，然后给本文件加上setuid标志。
2、安装python3的tkinter模块，命令： sudo apt-get install python3-tk
3、打开终端，在终端中输入命令：python3  绝对路径/Hosts助手.py  （注意！一定要是绝对路径）
4、成功，以后可以从启动器打开
"""

# !/usr/bin/python3
from multiprocessing import Process, Queue
import tkinter as tk
import pickle
import socket
import fcntl
import time
import sys
import re
import os
import requests


class Entry(object):
    """文本框类"""

    def __init__(self, n, root, skins, skin):
        self.url = tk.StringVar()
        self.root = root
        self.skins = skins
        self.skin = skin
        self.Entered = tk.Entry(self.root, fg=self.skins[self.skin][3], bg=self.skins[self.skin][0],
                                textvariable=self.url, highlightbackground=self.skins[self.skin][1], relief=tk.FLAT)
        self.Entered.grid(column=1, columnspan=2, row=n + 6,
                          padx=1, pady=1, sticky=tk.N + tk.E + tk.S + tk.W)

    def set_content(self, url):
        self.url.set(url)

    def get_content(self):
        return self.url.get()

    def set_fg(self, color):
        self.Entered['fg'] = color
        self.Entered.update()


class HOSTS(object):
    def __init__(self):
        """给软件设置初始参数"""
        self.version = 1.0
        self.x = 0
        self.y = 0
        self.auto = 0  # 0表示不自启
        self.skins = [('#1F2326', 'black', '#1F2336', '#00ffff', '#1F2336'),
                      ('#FFFFFF', '#90ee90', '#90ee90', '#00ced1', '#90ee90')]
        self.skin = 0
        self.urls = self.raw_urls = ['https://raw.githubusercontent.com/googlehosts/hosts/master/hosts-files/hosts',
                                     'https://raw.githubusercontent.com/racaljk/hosts/master/hosts',
                                     'https://git.oschina.net/lengers/connector/raw/master/hosts',
                                     '']
        self.entry = []  # 文本框对象列表
        self.button_list = []  # 按钮列表
        self.root = None
        self.label = None

    def set_hosts(self, n, q, flag):
        """更新hosts操作的子进程"""
        print('子进程开始')
        with open('/etc/hosts', 'w+') as f:
            if len(self.urls[n]) == 0:
                q.put({str(n): 1})
            else:
                try:
                    r = requests.get(url=self.urls[n], timeout=5)
                except:
                    q.put({str(n): 0})
                    print('url{}超时'.format(n))
                else:
                    fcntl.flock(f, fcntl.LOCK_EX)
                    if flag.empty():
                        flag.put(n)
                        hostname = socket.gethostname()
                        f.write(r.text.replace('hostname', hostname, 1))
                        fcntl.flock(f, fcntl.LOCK_UN)
                        q.put({str(n): 3})
                        print('已写入url{}的hosts'.format(n))
                    else:
                        q.put({str(n): 2})

    def update_hosts(self):
        """更新hosts操作的主进程"""
        if len(sys.argv) == 1:  # 判断是以后台运行还是带界面
            self.urls = [e.get_content() for e in self.entry]
            if re.match(r'^\s*$', ''.join(self.urls)):
                self.label.config(text='别逗我！所有地址都为空！')
                self.label.update()
            else:
                self.label.config(text='正在更新hosts，请等待')
                self.label.update()
                flag = Queue(1)
                q = Queue(4)
                if len(self.urls):
                    ps = []
                    for n in range(len(self.urls)):
                        p = Process(target=self.set_hosts, args=(n, q, flag))
                        ps.append(p)
                        p.start()
                    [p.join() for p in ps]

                    if flag.full():
                        self.label.config(text='hosts更新成功！')
                    else:
                        self.label.config(text='更新失败，请重试')
                    self.label.update()

                    dic = {}
                    for _ in range(4):
                        dic.update(q.get())
                    for n in range(4):
                        self.entry[n].set_fg(
                            ('red', '#00ffff', '#00ffff', '#00ff00')[dic.get(str(n))])
        else:
            if len(self.urls):
                flag = Queue(1)
                while flag.empty():
                    ps = []
                    q = Queue(4)
                    for n in range(len(self.urls)):
                        p = Process(target=self.set_hosts, args=(n, q, flag))
                        ps.append(p)
                        p.start()
                    time.sleep(180)
                    [p.join() for p in ps]
                exit()
            else:
                exit()

    def get_config(self):
        """如果有配置文件，就从配置文件获取配置，否则创建配置文件"""
        if os.path.exists(sys.path[0] + '/config.pkl'):
            with open(sys.path[0] + '/config.pkl', 'rb') as config:
                dic = pickle.load(config)
            self.auto = dic.get('auto')
            self.urls = dic.get('urls')
            self.skin = dic.get('skin')
            self.x = dic.get('x')
            self.y = dic.get('y')
        else:
            # 启动器图标所需内容,下面StartupWMClass作用是让任务栏只有一个图标，即使在任务栏创建了图标
            content = """[Desktop Entry]
Encoding=UTF-8
Name=Hosts助手
StartupWMClass=Tk
Comment=帮助更新Hosts文件
Exec=python3 "{}"
Icon = "{}"
Categories=Application;
Version={}
Type=Application
Terminal=false
""".format(os.path.realpath(__file__), sys.path[0] + '/ICON.png', self.version)
            path = os.environ['HOME'] + \
                   '/.local/share/applications/' + 'Hosts_assistant.desktop'
            with open(path, 'w+') as f:
                f.write(content)

            # 创建run.sh脚本
            command = """#!/bin/sh
if [ -e {0} ]; then
    sleep 1m
    python3 "{0}" 1
fi
            """.format(os.path.realpath(__file__))
            with open(sys.path[0] + '/run.sh', 'w+') as f:
                f.write(command)

            # 保存原始hosts文件
            with open('/etc/hosts', 'r') as f:
                raw_hosts = f.read()
            with open(sys.path[0] + '/raw_hosts.pkl', 'wb') as f:
                pickle.dump(raw_hosts, f)

    def save_config(self, e):
        """保存配置到配置文件"""
        self.x = self.root.winfo_x()
        self.y = self.root.winfo_y() - 28
        self.urls = [e.get_content() for e in self.entry]
        dic = {'auto': self.auto, 'urls': self.urls,
               'skin': self.skin, 'x': self.x, 'y': self.y}
        with open(sys.path[0] + '/config.pkl', 'wb') as config:
            pickle.dump(dic, config)

    def restore_hosts(self):
        """将hosts文件重置到原始"""
        with open(sys.path[0] + '/raw_hosts.pkl', 'rb') as config:
            raw_hosts = pickle.load(config)
        with open('/etc/hosts', 'w+') as f:
            f.write(raw_hosts)
        self.label.config(text='hosts已经还原到最初！')

    def restore_urls(self):
        """将url列表重置为默认"""
        for n in range(4):
            self.entry[n].set_content(self.raw_urls[n])
            self.entry[n].set_fg(self.skins[self.skin][3])
        self.label.config(text='地址重置成功！')

    def dialog(self):
        """显示软件说明"""

        def close_dialog(e):
            dialog.destroy()

        dialog = tk.Toplevel(self.root)
        dialog.overrideredirect(True)
        dialog.geometry(
            '+{}+{}'.format(self.root.winfo_screenwidth() // 2 - 180, self.root.winfo_screenheight() // 2 - 135))
        dialog["background"] = self.skins[self.skin][0]
        dialog.resizable(False, False)
        dialog.wm_attributes('-topmost', 1)
        content = """    软件：Hosts助手    软件版本：{}     作者：杰哥
    说明：hosts文件源来自互联网，本人不保证安全，可自行修改。
    如果修改后发现有问题，可以点击还原hosts按钮，还原到最初。
    替换hosts文件后可能不会立即生效，可以关闭/开启网络，或
    启用/禁用飞行模式让域名解析立即生效。
    开机自启表示软件会在开机时在后台启动并自动更新hosts，直
    到成功。软件选择地址列表中连接最快的作为源文件，各源内容
    不相同。更新hosts完成后，地址显示红色的表示超时或者失效，
    显示绿色的表示最终的hosts文件来源。"""
        sub_label = tk.Label(dialog, text=content.format(self.version),
                             justify=tk.LEFT, anchor=tk.W, fg=self.skins[self.skin][3], relief=tk.FLAT,
                             highlightthickness=0.4, bg=self.skins[self.skin][0], width=51, height=10)
        sub_label.bind('<Button-1>', close_dialog)
        sub_label.pack()

    def auto_starts(self):
        """设置是否开机启动，自动更新"""
        PATH = os.environ['HOME'] + '/.profile'
        content = """
# For Hosts assistant
if [ -e "{0}" ]; then
    . {0} &
fi"""
        script = content.format(sys.path[0] + '/run.sh')
        if self.auto == 0:
            self.auto = 1
            with open(PATH, 'a') as f:
                f.write(script)
        else:
            self.auto = 0
            with open(PATH, 'r+') as f:
                result = f.read().replace(script, '')
                f.truncate(0)
                f.seek(0, 0)
                f.write(result)
        self.button_list[3]['text'] = ('开机自启', '取消自启')[self.auto]

    def change_skin(self):
        """切换皮肤"""
        self.skin = (self.skin + 1) % len(self.skins)
        self.root.destroy()
        print(os.path.realpath(__file__))
        os.system('python3 "{}"'.format(os.path.realpath(__file__)))
        print('到此一游')

    def ui(self):
        """启动软件主界面"""
        self.root = tk.Tk()
        self.root.title('Hosts助手')

        img = tk.PhotoImage(file=sys.path[0] + '/ICON.png')
        self.root.tk.call('wm', 'iconphoto', self.root._w, img)

        if self.x == self.y == 0:
            self.x = self.root.winfo_screenwidth() // 2 - 100
            self.y = self.root.winfo_screenheight() // 2 - 200
        self.root.geometry('+{}+{}'.format(self.x, self.y))
        self.root["background"] = self.skins[self.skin][0]
        self.root.resizable(False, False)  # 固定窗口大小
        self.root.wm_attributes('-topmost', 1)  # 置顶窗口
        # self.root.overrideredirect(True)

        self.label = tk.Label(self.root, text='提示框', fg=self.skins[self.skin][3], font=("Arial, 12"),
                              relief=tk.FLAT, bg=self.skins[self.skin][2], width=22, pady=5)
        self.label.grid(column=1, columnspan=2, row=1)
        self.label.bind('<Destroy>', self.save_config)  # 添加退出事件

        lst = [('立即更新', self.update_hosts, 1, 2), ('还原hosts', self.restore_hosts, 2, 2),
               ('切换主题', self.change_skin, 1, 3), (('开机自启', '取消自启')
                                                  [self.auto], self.auto_starts, 2, 3),
               ('重置地址', self.restore_urls, 1, 4), ('软件说明', self.dialog, 2, 4)]
        for t in lst:
            button = tk.Button(self.root, text=t[0], relief=tk.FLAT, command=t[1], fg=self.skins[self.skin][3],
                               bg=self.skins[self.skin][0], activebackground=self.skins[self.skin][4],
                               highlightthickness=0.5, activeforeground=self.skins[self.skin][3],
                               highlightbackground=self.skins[self.skin][1])
            button.grid(column=t[2], row=t[3], padx=1,
                        pady=1, sticky=tk.N + tk.E + tk.S + tk.W)
            self.button_list.append(button)

        frame = tk.Frame(self.root, bg=self.skins[self.skin][0], height=10)
        frame.grid(row=5)

        for n in range(4):
            self.entry.append(Entry(n, self.root, self.skins, self.skin))
            self.entry[n].set_content(self.urls[n])

        self.root.mainloop()

    def start(self):
        """开始执行，根据命令行参数，决定是后台执行还是启动界面"""
        self.get_config()
        if len(sys.argv) == 1:
            self.ui()
        else:
            self.update_hosts()


if __name__ == "__main__":
    HOSTS().start()
