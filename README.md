# 股票、基金的估值及监控

基于东方财富API实现的的估值查询及定时监控，可定时推送消息。

包含功能：

* [命令行交互](#command)
* [网络请求查询](#http)
* [定时推送](#schedule)

# TODO

1. [x] 多线程
2. [x] 监控股票基金的成本涨跌幅、净值阈值
   1. [x] 避免每日重复告警

# 安装

1. 下载源码
    ```shell
    git clone https://github.com/fevolq/Money.git
    ```

2. 安装依赖
    ```shell
    pip install -r requirements.txt
    ```

3. 启动（详见[使用指南](#guidance)）

# 内部设计

1. 通过**指定类型** `(fund/stock)` 和**指定代码**，可直接查询估值等数据
2. 通过预先关注，可快捷查询关注列表中的估值等数据

# <a id="guidance">使用指南</a>

## <a id="command">命令行</a>

* 入口文件：`command.py`

### 估值查询

* 直接查询
    ```shell
  # python command.py -t <类型> -c <代码>
  
  # 示例：查询基金：000001、000003
  python command.py -t 'fund' -c '000001,000003'
    ```
* 查询关注
  ```shell
  # python command.py -t <类型>
    
  # 示例：查询所关注的基金
  python command.py -t 'fund'
  ```
  注：
    * -t: 类型 `<type>`。`fund: 基金；stock: 股票`
    * -c: 代码 `<code>`

### （估值）关注配置

```bash
python command.py --command=<操作类型> -t <类型> [-c <代码>]

# 示例：查询关注的基金
python command.py --command='get' -t 'fund'

# 示例：增加关注的基金：000001、000003
python command.py --command='add' -t 'fund' -c '000001,000003'

# 示例：删除某个关注的基金：000001、000003
python command.py --command='delete' -t 'fund' -c '000001,000003'
```

## <a id="http">http请求</a>

* 入口文件：`app.py`

注：

* 附带[定时推送](#schedule)功能

### 启动

* 直接启动：`python app.py`
* 基于uvicorn：`uvicorn app:app`
* 容器化：
    * 构建镜像：`docker build -t <image_name> .`，也可使用以构建好的镜像：`docker pull infq/money`
    * 启动容器：`docker run -d --name=<container_name> -p 8888:8888 <image_id>`
    * 可选参数：
        * `-e PORT=<port>`: 指定启动端口
        * `-v <本地路径>:/data/money/data`: 数据文件夹
        * `-v <本地路径>:/data/money/conf`: 配置文件夹

### 估值查询

```text
curl -X GET "http://127.0.0.1:8888/search/${type}" --data "codes=${codes}"

# 示例：查询基金：000001、000003
http://127.0.0.1:8888/search/fund?codes=000001,000003

# 示例：查询所关注的基金
http://127.0.0.1:8888/search/fund
```

### 估值配置

```text
curl -X GET "http://127.0.0.1:8888/focus/worth/${type}/${command}" --data "codes=${codes}"

# 示例：查询关注的基金
http://127.0.0.1:8888/focus/worth/fund/get

# 示例：增加关注的基金：000001、000003
http://127.0.0.1:8888/focus/worth/fund/add?codes=000001,000003

# 示例： 删除某个关注的基金：000001、000003
http://127.0.0.1:8888/focus/worth/fund/delete?codes=000001,000003
```

### 监控配置

```text
curl -X GET "http://127.0.0.1:8888/focus/monitor/${type}/${command}" --data "code=${code}"
# 可选参数：code: 代码，worth: 净值阈值（+/-），cost: 成本，growth: 涨幅，lessen: 跌幅，remark: 备注，ids: 需要删除的配置的id

# 示例：查询监控的基金
http://127.0.0.1:8888/focus/monitor/fund/get

# 示例：增加监控的基金：000001，阈值为2（估值大于等于2时）
http://127.0.0.1:8888/focus/monitor/fund/add?code=000001&worth=2&remark=测试
# 示例：增加监控的基金：000001，阈值为2（估值小于等于2时）
http://127.0.0.1:8888/focus/monitor/fund/add?code=000001&worth=-2&remark=测试
# 示例：增加监控的基金：000001，涨幅为5，跌幅为10。（需要成本参数）
http://127.0.0.1:8888/focus/monitor/fund/add?code=000001&cost=1.5&growth=5&lessen=10

# 示例： 删除某个监控的基金配置：123、456
http://127.0.0.1:8888/focus/monitor/fund/delete?ids=123,456
```

## <a id="schedule">定时推送</a>

* 入口文件：`scheduler.py`

### 启动

* 直接启动：`python scheduler.py`
* 依赖于app：通过开启 http 服务来启动。详见 [http请求](#http)

### 其他

* 配置文件：conf/config.yaml
    * FeiShuRobotUrl: [飞书群的机器人地址](https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot)
    * ChanKey: [Server酱服务的key](https://sct.ftqq.com/)
    * FundCron: 基金的定时任务（[crontab格式](https://crontab.guru/#*_*_*_*_*)）
    * StockCron: 股票的定时任务（crontab格式）
