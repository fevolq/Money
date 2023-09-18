# 股票、基金的估值及监控

基于东方财富API实现的的估值查询及定时监控，可定时推送消息。


# TODO

1. [x] 多线程
2. [x] 监控股票基金的成本涨跌幅、净值阈值
   1. [x] 避免每日重复告警
3. [x] 估值查询增加缓存层
4. [x] 代码与名称的对应增加缓存层
5. [x] restful
6. [x] 前端页面


# 架构

## 内部设计

1. 通过**指定类型** `(fund/stock)` 和**指定代码**，可直接查询估值等数据
2. 通过配置关注，可实现快捷查询
3. 增加监控配置，可在指定时间自动查询数据，并推送达到要求的配置信息

## 交互方式

* [命令行交互](#command)
* [网络请求查询](#http)
* [定时推送](#schedule)


# 使用指南

## <a id="command">命令行</a>

* 入口文件：`command.py`
* 包含功能：
  * 估值查询
  * 配置关注列表

### 估值查询
`python command.py -t <类型> -c <代码>`

```shell
# 查询指定代码
## 示例：查询基金：000001、000003
python command.py -t 'fund' -c '000001,000003'

# 查询关注
## 示例：查询所关注的基金
python command.py -t 'fund'
```

注：
* -t: 类型 `<type>`。`fund: 基金；stock: 股票`
* -c: 代码 `<code>`


### 配置关注
`python command.py --command=<操作类型> -t <类型> [-c <代码>]`

```shell
# 示例：查询关注的基金
python command.py --command='get' -t 'fund'

# 示例：增加关注的基金：000001、000003
python command.py --command='add' -t 'fund' -c '000001,000003'

# 示例：删除某个关注的基金：000001、000003
python command.py --command='delete' -t 'fund' -c '000001,000003'
```

## <a id="http">http请求</a>

* 入口文件：`app.py`
* 功能：
  * 估值查询
  * 配置关注
  * 配置监控

注：

* 附带 [定时推送](#schedule) 功能
* api 接口均已增加对应 restful 接口（原接口暂时保留）。原接口去除掉 command 参数，更换对应请求方式与其他传参格式即可。
    
  如：
    ```text
    # 示例：增加监控的基金：000001，阈值为2（估值大于等于2时）
  
    # 原接口
    http://127.0.0.1:8888/focus/monitor/fund/add?code=000001&worth=2&remark=测试

    # restful 接口
    curl -X POST "http://127.0.0.1:8888/focus/monitor/fund" --data "codes=${codes}"
    -H "Content-Type: application/json"
    -d '{"code": "000001", "worth": 2, "remark": "测试"}'
    ```

### 启动

* 直接启动：`python app.py`
* 基于uvicorn：`uvicorn app:app`
* 基于docker：
    * 构建镜像：`docker build -t <image_name> .`（或 `docker pull infq/money`）
    * 启动容器：`docker run -d --name=<container_name> -p 8888:8888 <image_id>`
    * 可选参数：
        * `-e PORT=<port>`: 指定启动端口
        * `-v <本地路径>:/data/money/data`: 数据文件夹
        * `-v <本地路径>:/data/money/conf`: 配置文件夹
* 基于docker-compose：`docker-compose up -d`

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
http://127.0.0.1:8888/focus/monitor/fund/get?code=000001

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
* 功能：
  * 推送关注列表的估值
  * 监控估值及涨跌幅

### 启动

* 直接启动：`python scheduler.py`
* 依赖于app：通过开启 http 服务来启动。详见 [http请求](#http)


# 其他
## 前端界面
本项目当前仅提供后端接口，需要前端界面可通过以下方式：
1. docker-compose 方式启动 http 服务
2. 使用提供的前端镜像：`docker pull infq/money-front`
3. Code by youself

## 配置文件
* FeiShuRobotUrl: [飞书群的机器人地址](https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot)
* ChanKey: [Server酱服务的key](https://sct.ftqq.com/)
* FundWorthCron: 基金的定时任务（[crontab格式](https://crontab.guru/#*_*_*_*_*)）
* StockWorthCron: 股票的定时任务（crontab格式）
* FundMonitorCron: 股票的监控任务（crontab格式）
* StockMonitorCron: 股票的监控任务（crontab格式）
