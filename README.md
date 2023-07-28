# 股票、基金的估值
基于东方财富网API实现的的估值查询功能，可通过 `命令行` 、`网络请求` 等进行交互。

# TODO
1. api接口交互
2. 信息通知
3. 服务部署（定时查询关注）

# 内部设计
1. 通过指定类型 `(fund/stock)` 和指定代码，可直接查询估值等数据
2. 通过预先关注，可快捷查询关注列表中的估值等数据

# 使用指南

## 命令行
* 入口文件：`command.py`

### 查询操作
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

### 关注操作
```shell
python command.py --command=<操作类型> -t <类型> [-c <代码>]

# 示例：查询关注的基金
python command.py --command='get' -t 'fund'

# 示例：增加关注的基金：161725、003096
python command.py --command='add' -t 'fund' -c '161725,003096'

# 示例：删除某个关注的基金：161725、003096
python command.py --command='delete' -t 'fund' -c '161725,003096'
```

## http请求
* 入口文件：`app.py`

### 启动
* 直接启动：`python app.py`
* 基于uvicorn：`uvicorn app:app`

### 查询
```text
curl -X GET "http://127.0.0.1:8000/search/${type}" --data "codes=${codes}"

# 示例：查询基金：161725、003096
http://127.0.0.1:8000/search/fund?codes=161725,003096

# 示例：查询所关注的基金
http://127.0.0.1:8000/search/fund
```

### 关注
```text
curl -X GET "http://127.0.0.1:8000/watch/${command}" --data "type=${type}&codes=${codes}"

# 示例：查询关注的基金
http://127.0.0.1:8000/watch/get?type=fund

# 示例：增加关注的基金：161725、003096
http://127.0.0.1:8000/watch/add?type=fund&codes=161725,003096

# 示例： 删除某个关注的基金：161725、003096
http://127.0.0.1:8000/watch/delete?type=fund&codes=161725,003096
```