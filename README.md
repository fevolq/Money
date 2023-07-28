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
# python command.py --command=<操作类型> -t <类型> [-c <代码>]

# 示例：
# 查询关注的基金
python command.py --command='get' -t 'fund'

# 增加关注的基金：161725、003096
python command.py --command='add' -t 'fund' -c '161725,003096'

# 删除某个关注的基金：161725、003096
python command.py --command='delete' -t 'fund' -c '161725,003096'
```