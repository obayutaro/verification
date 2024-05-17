import asyncio
import websockets
from web3 import Web3
import json
import mysql.connector

host = "localhost"
user = "root"
password = "hcdzh3yx"
database = "lottery"
# MySQLに接続
conn = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database
)

# 接続が成功したらcursorを取得
if conn.is_connected():
    cursor = conn.cursor()

cursor.execute('DELETE FROM product_number_count;')
cursor.execute('DELETE FROM product_name_count;')
cursor.execute('DELETE FROM lottery_info;')

# Ganache WebSocketのエンドポイント
w3 = Web3(Web3.WebsocketProvider("ws://127.0.0.1:7545"))

# コントラクトアドレス
contract_addresses = [
    "0x2485b8496fd2BCd82426f3D2B957455B9A811162"
]

# コントラクトABI
contract_abi = [
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": False,
				"name": "normal",
				"type": "uint64"
			},
			{
				"indexed": False,
				"name": "rare",
				"type": "uint64"
			},
			{
				"indexed": False,
				"name": "ultimate",
				"type": "uint64"
			},
			{
				"indexed": False,
				"name": "maxNumber",
				"type": "uint64"
			},
			{
				"indexed": False,
				"name": "name",
				"type": "string"
			}
		],
		"name": "ReturnProbability",
		"type": "event"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": False,
				"name": "setting_block_Number",
				"type": "uint64"
			},
			{
				"indexed": False,
				"name": "randomNumber",
				"type": "uint64[]"
			},
			{
				"indexed": False,
				"name": "prize_no",
				"type": "uint8[]"
			}
		],
		"name": "Acquired_product_description",
		"type": "event"
	}
]

# イベント名の取得
event_names = [event["name"] for event in contract_abi if event["type"] == "event"]

# フィルターとコントラクトの対応を辞書で管理
contract_filters = {}
for contract_address in contract_addresses:
    contract = w3.eth.contract(address=contract_address, abi=contract_abi) #コントラクトのインスタンス生成
    contract_filters[contract_address] = {
        event_names[0]: contract.events[event_names[0]].create_filter(fromBlock="latest"),
        event_names[1]: contract.events[event_names[1]].create_filter(fromBlock="latest")
}

# 設定ログ取得とsqlサーバでのリストの作成
product_name = ["Normal","Rare","Ultimate"]
def handle_event_setting(log):
    print("setting")
    event_normal = log["args"]["normal"]
    event_rare = log["args"]["rare"]
    event_ultimate = log["args"]["ultimate"]
    event_max = log["args"]["maxNumber"]
    BN = log["blockNumber"]
    event_name = log["args"]["name"]
    
    #抽選名テーブル
    cursor.execute('INSERT INTO lottery_info (lottery_id, lottery_name) VALUES (%s, %s)', (BN, event_name))
    #当選番号テーブル
    for i in range(event_max):
        product_number = i+1
        cursor.execute('INSERT INTO product_number_count (lottery_id, product_number, count) VALUES (%s, %s, 0)', (BN, product_number))
    #当選順位テーブル
    if event_normal != 0 and event_rare != 0 and event_ultimate != 0:
        for i in product_name:
            cursor.execute('INSERT INTO product_name_count (lottery_id, product_name, count) VALUES (%s, %s, 0)', (BN, i))
    # 変更を保存
    conn.commit()

# 抽選ログの取得とsqlサーバ内でカウント
def handle_event_lottery(log):
    print("lottery")
    event_setting_block_Number = log["args"]["setting_block_Number"]
    event_randomNumber = log["args"]["randomNumber"]
    event_prize = log["args"]["prize_no"]
    
    #当選番号カウント
    for i in event_randomNumber:
        cursor.execute('UPDATE product_number_count SET count = count + 1 WHERE lottery_id = %s and product_number = %s;', (event_setting_block_Number,i))
    if 0 in event_prize:
        print("当選順位を含まない")
    else:
        #当選順位カウント
        for i in event_prize:
            if i==3:
                p = product_name[0]
            elif i==2:
                p = product_name[1]
            elif i==1:
                p = product_name[2]
            cursor.execute('UPDATE product_name_count SET count = count + 1 WHERE lottery_id = %s and product_name = %s;', (event_setting_block_Number,p))
    # 変更を保存
    conn.commit()


async def log_loop():
    async with websockets.connect('ws://localhost:7545') as ws:
        for contract_address in contract_addresses:
            subscription_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_subscribe",
                "params": ["logs", {"address": contract_address}] #, "topics": [contract_filters[contract_address][event_names[0]].filter_params['topics'], contract_filters[contract_address][event_names[1]].filter_params['topics']]
            }
            await ws.send(json.dumps(subscription_msg))
            response = await ws.recv()
            
                
        while True:
            print("-------------------------------------------------------------------------------")
            respons = await ws.recv() #通知を待つ
            for contract_address, filters in contract_filters.items(): #ログをgetする
                for log in filters[event_names[0]].get_new_entries():
                    handle_event_setting(log)
                for log in filters[event_names[1]].get_new_entries():
                    handle_event_lottery(log)

async def main():
    print("start")
    await log_loop()
    # 接続を閉じる
    cursor.close()
    conn.close()

if __name__ == '__main__':
    asyncio.run(main())