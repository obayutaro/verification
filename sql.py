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
    
lottery_name = input("抽選名を入力：")
# lottery_nameに対応するlottery_idを取得
cursor.execute('SELECT lottery_id FROM lottery_info WHERE lottery_name = %s', (lottery_name,))
lottery_id = cursor.fetchone()

if lottery_id:
    lottery_id = lottery_id[0]

    # 商品番号のカウント数の合計を取得
    cursor.execute('SELECT SUM(count) FROM product_number_count WHERE lottery_id = %s', (lottery_id,))
    sum_no = cursor.fetchone()[0]

    # 商品名のカウント数の合計を取得
    cursor.execute('SELECT SUM(count) FROM product_name_count WHERE lottery_id = %s', (lottery_id,))
    sum_name = cursor.fetchone()[0]

    cursor.execute('select count(product_number) from product_number_count where lottery_id = %s', (lottery_id,))
    count_no = cursor.fetchone()[0]
    print(count_no)
    for i in range(count_no):
        cursor.execute('select count from product_number_count where product_number = %s',(i+1,))
        probability_conut = cursor.fetchone()[0] / sum_no
        print(f"{i+1}：{probability_conut}")
        
    product_name = ["Normal","Rare","Ultimate"]
    for i in product_name:
        cursor.execute('select count from product_name_count where product_name = %s',(i,))
        probability_conut = cursor.fetchone()[0] / sum_no
        print(f"{i}の確率：{probability_conut}")
    
    print(f"lottery_name: {lottery_name}")
    print(f"商品番号のカウント数合計: {sum_no}")
    print(f"商品名のカウント数合計: {sum_name}")
# 変更を保存
conn.commit()

# 接続を閉じる
cursor.close()
conn.close()
