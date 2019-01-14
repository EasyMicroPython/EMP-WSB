# EMP WSB
该项目是 EMP-IDE 串口连接的转发工具，用于将串口的数据向浏览器进行实时的转发。


## Quick Start
```python
from wsb import WSB

wsb = WSB('/dev/ttyUSB0')
wsb.start()
```

上面的代码运行之后，便会在本地开启一个 `WebSocket Server`，默认端口 `9000`, 在浏览器端的 `EMP-IDE` 便可以使用串口连接方式，与你的MicroPython设备进行连接了。