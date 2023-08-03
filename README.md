# 股票、基金的估值

基于东方财富API实现的的估值查询，可定时推送消息。

包含功能：

* [命令行交互](#command)
* [网络请求查询](#http)
* [定时推送](#schedule)

# TODO

<input type="checkbox" checked> 多线程<br>
<input type="checkbox" > 监控股票基金的成本涨跌幅、净值阈值<br>

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

### 查询

* 直接查询
    ```shell
  # python command.py -t <类型> -c <代码>
  
  # 示例：查询基金：161725、003096
  python command.py -t 'fund' -c '161725,003096'
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

### 关注

```bash
python command.py --command=<操作类型> -t <类型> [-c <代码>]

# 示例：查询关注的基金
python command.py --command='get' -t 'fund'

# 示例：增加关注的基金：161725、003096
python command.py --command='add' -t 'fund' -c '161725,003096'

# 示例：删除某个关注的基金：161725、003096
python command.py --command='delete' -t 'fund' -c '161725,003096'
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
        * `-v <本地路径>:/data/money/data`: 数据文件
        * `-v <本地路径>:/data/money/conf`: 配置文件

### 查询

```text
curl -X GET "http://127.0.0.1:8888/search/${type}" --data "codes=${codes}"

# 示例：查询基金：161725、003096
http://127.0.0.1:8888/search/fund?codes=161725,003096

# 示例：查询所关注的基金
http://127.0.0.1:8888/search/fund
```

### 关注

```text
curl -X GET "http://127.0.0.1:8888/watch/${command}" --data "type=${type}&codes=${codes}"

# 示例：查询关注的基金
http://127.0.0.1:8888/watch/get?type=fund

# 示例：增加关注的基金：161725、003096
http://127.0.0.1:8888/watch/add?type=fund&codes=161725,003096

# 示例： 删除某个关注的基金：161725、003096
http://127.0.0.1:8888/watch/delete?type=fund&codes=161725,003096
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
