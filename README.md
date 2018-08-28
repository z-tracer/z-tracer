# z-tracer
  z-tracer是一个分布式的linux性能监测工具。可以用来实时观测linux系统运行情况，分析系统热点，代码执行流程。z-tracer既能支持主机系统，也可以支持嵌入式系统。嵌入式系统通常cpu能力和内存大小有限，不适合进行数据分析和数据存储。z-tracer通过设备->服务器的分布式方式，将数据分析和处理移到性能更高的服务器端，减轻设备压力。z-tracer可以同时监控多个设备。
![image](http://z-tracer.github.io/img/top.jpg)<br>
上图是z-traced的整体框架，在设备上运行ztracerd服务，服务器端通过jsonrpc与设备通信，采集设备信息，同时进行数据分析和处理。服务器端采用flask框架，好处是能够同时支持windows和linux。用户通过浏览器访问服务器获取分析数据。

## 安装
### 设备端
设备端需要运行一个服务程序：ztracerd
  在ztracerd/目录下执行（如果是交叉编译，需要修改工具链）:
```Bash
  make
```

### 服务器端
服务器端需要建立python + flask环境
* 建立虚拟环境，cd到工程目录执行：
```Bash
    python -m venv venv
```

* 激活虚拟环境
```Bash
    source venv/bin/activate   (linux环境)
    .venv\Scripts\activate   (windows环境)
```

* 安装依赖包
```Bash
    pip install -r requirements.txt
```

* 运行
```Bash
    ./manage.py runserver -h xxx.xxx.xxx.xxx -p xx       (linux环境)
    python manage.py runserver -h xxx.xxx.xxx.xxx -p xx  (windows环境)
```

z-tracer帮助：http://z-tracer.github.io
