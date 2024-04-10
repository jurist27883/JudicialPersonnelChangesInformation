import sys
import os
import csv
from datetime import datetime, timedelta
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

def save_table_to_csv(file_name, file_date, source_table, csv_writer):
    """テーブルデータをCSVファイルに保存する関数"""

    # ファイル名の末尾1字から組織を取得
    last_character = os.path.splitext(file_name)[0][-1]
    if last_character == "s":
        organization = "裁判所"
    elif last_character == "j":
        organization = "法務省"
    else:
        organization = "その他"

    # 1列目にファイル名の冒頭8文字を格納し、2列目に組織を、3列目以降に表のデータを格納する
    for row in source_table.find_all('tr'):
        #表のデータを取得
        cells = [cell.get_text(strip=True) for cell in row.find_all(['th', 'td'])]

        #任地データを分割
        posts = split_text_between_parenthese(cells[1])

        # ファイル名の冒頭8文字を取得し、その後に表のデータを格納
        csv_writer.writerow([file_date] + [organization] + [cells[0]] +[post for post in posts])

def split_text_between_parenthese(string):
    """文字列を括弧で分割する関数"""
    parenthese = 0
    right_position  = 0

    for char in reversed(string):
        match char:
            case  ')' | '）':
                parenthese += 1
            case  '(' | '（':
                parenthese -= 1
        right_position += 1
        if parenthese == 0:
            break

    ln = len (string)
    return [string[:ln-right_position],string[ln-right_position+1:-1]]

# URLを指定
url = "https://www.westlawjapan.com/p_affairs/"
# ページの内容を取得
response = requests.get(url,timeout=10)

# ステータスコードが正常でない場合、エラーを出力してプログラムを終了
if response.status_code != 200:
    print("Failed to retrieve page")
    sys.exit()

# BeautifulSoupを使ってHTMLを解析
soup = BeautifulSoup(response.text, "html.parser")

# 今日の日付を取得
today = datetime.now().strftime("%Y%m%d")
now = datetime.now().strftime("%H%M%S")

# CSVファイルを開く
with open("data_" + today[2:] + now + ".csv", 'w', newline='', encoding='utf-8-sig') as csvfile:
    writer = csv.writer(csvfile)

    #タイトル行作成
    writer.writerow(["更新日"] + ["組織"] + ["氏名"] + ["異動先"] + ["前任地"])

    # 3か月前の日付を計算
    three_months_ago = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")

    # リンク先のHTMLを処理
    for link in soup.find_all('a'):
        href = urljoin("https://www.westlawjapan.com/p_affairs/",link.get('href'))
        # リンク先のファイル名の冒頭8文字が3か月以内の場合に処理を実行
        file_name = os.path.basename(href)
        file_date = file_name[:8]
        if file_date > three_months_ago and file_date <= today:
            # リンク先のHTMLを取得
            response = requests.get(href,timeout=10)
            if response.status_code == 200:
                soup_subpage = BeautifulSoup(response.text, "html.parser")
                table = soup_subpage.find("table")
                if table:
                    # 表のデータをCSVファイルに追加
                    save_table_to_csv(file_name, file_date, table, writer)
                    print(f"Table data from {file_date} has been added to all_table_data.csv")
    print("Completed!")
    