# canal_demo.py
import time

from canal.client import Client
from canal.protocol import EntryProtocol_pb2
from canal.protocol import CanalProtocol_pb2

# 建立与canal服务端的连接
client = Client()
client.connect(host='127.0.0.1', port=11111)   # canal服务端部署的主机IP与端口
client.check_valid(username=b'canal', password=b'canal')  # 自行填写配置的数据库账户密码
# destination是canal服务端的服务名称， filter即获取数据的过滤规则，采用正则表达式
client.subscribe(client_id=b'1001', destination=b'example', filter=b'.*\\..*')

while True:
    message = client.get(100)
    # entries是每个循环周期内获取到数据集
    entries = message['entries']
    for entry in entries:
        entry_type = entry.entryType
        if entry_type in [EntryProtocol_pb2.EntryType.TRANSACTIONBEGIN, EntryProtocol_pb2.EntryType.TRANSACTIONEND]:
            continue
        row_change = EntryProtocol_pb2.RowChange()
        row_change.MergeFromString(entry.storeValue)
        event_type = row_change.eventType
        header = entry.header
        # 数据库名
        database = header.schemaName
        # 表名
        table = header.tableName
        event_type = header.eventType
        # row是binlog解析出来的行变化记录，一般有三种格式，对应增删改
        for row in row_change.rowDatas:
            format_data = dict()
            # 根据增删改的其中一种情况进行数据处理
            if event_type == EntryProtocol_pb2.EventType.DELETE:
                format_data['before'] = dict()
                for column in row.beforeColumns:
                    #format_data = {
                    #    column.name: column.value
                    #}
                    #此处注释为原demo，有误，下面是正确写法
                    format_data['before'][column.name] = column.value
            elif event_type == EntryProtocol_pb2.EventType.INSERT:
                format_data['after'] = dict()
                for column in row.afterColumns:
                    #format_data = {
                    #    column.name: column.value
                    #}
                    #此处注释为原demo，有误，下面是正确写法
                    format_data['after'][column.name] = column.value
            else:
                # format_data['before'] = format_data['after'] = dict()  采用下面的写法应该更好
                format_data['before'] = dict()
                format_data['after'] = dict()
                for column in row.beforeColumns:
                    format_data['before'][column.name] = column.value
                for column in row.afterColumns:
                    format_data['after'][column.name] = column.value
            # data即最后获取的数据，包含库名，表明，事务类型，改动数据
            data = dict(
                db=database,
                table=table,
                event_type=event_type,
                data=format_data,
            )
            print(data)
    time.sleep(1)

client.disconnect()
