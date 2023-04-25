import numpy as np
import pandas as pd
import re
import sys

# 英和辞書データ EDICT2
df_ejd = pd.read_table('edict/edict',names=['RAWデータ'],header=1)
# 強制変換単語
df_forcewk = pd.read_csv('強制変換単語.csv')
# OC辞書
df_oc = pd.read_excel('dictionary_OC.xls', usecols=(range(0,3)),header=1, names=('日本語項目名','強制変換単語','別名'))
# 強制変換単語 → OC辞書の順に結合し、重複除去
df_force = pd.concat([df_forcewk, df_oc[~df_oc['強制変換単語'].isnull()]], sort=False).groupby('日本語項目名').head(1)

# mecab 連携（要インストール）
import sys
import MeCab
mecab = MeCab.Tagger("-Ochasen")

# 漢字ローマ字変換（KAKASI）（要インストール）
from pykakasi import kakasi

kakasi = kakasi()

kakasi.setMode('H', 'a')
kakasi.setMode('K', 'a')
kakasi.setMode('J', 'a')

conv = kakasi.getConverter()


def search_dic(word):
    '''
    見出し語を検索し、語釈から先頭語釈を抽出
    '''
#    df_hit = df[df['RAWデータ'].str.contains(word)]
    df_hit = df_ejd[df_ejd['RAWデータ'].str.startswith(word)]
    # 事前処理'/(not)'をエスケープ → 廃止（語釈の分割後の補正処理で対応）
#    df_hit['RAWデータ'] = df_hit['RAWデータ'].str.replace('\(not\)', '{not}')
#    print(df_hit)

    # 列分割するにあたり、見出し語読み（[]）の有無で正規表現を分ける
    df_yomi_ari = df_hit[df_hit['RAWデータ'].str.contains('\[')]
    df_yomi_nashi = df_hit[~df_hit['RAWデータ'].str.contains('\[')]
    # 読みあり： 分割（[]で見出語を抽出
#    df_hit = df_hit['RAWデータ'].str.extract('(.*?)\s\[(.*)\]\s/(.*)' ,expand=True)
    df_yomi_ari = df_yomi_ari['RAWデータ'].str.extract('(?P<見出し語>.*?)\s\[(?P<見出し読み>.*)\]\s(?P<語釈>.*)' ,expand=True)
    # 読み無し： 分割（/(で見出語を抽出
    df_yomi_nashi = df_yomi_nashi['RAWデータ'].str.extract('(?P<見出し語>.*?)(?P<見出し読み>\s)/\((?P<語釈>.*)' ,expand=True)
    df_yomi_nashi['語釈'] = df_yomi_nashi['語釈'].apply(lambda x: '/(' + x)  #セパレータとした /( を補完
    # コンカチ
    df_hit = pd.concat([df_yomi_ari, df_yomi_nashi]).sort_index()
    # 語釈の末尾の(P),/を除去
    df_hit['語釈'] = df_hit['語釈'].replace('(.*?)(/$|/\(P\)/$)', r'\1', regex=True)
    # 事後処理（語釈がないエントリがあるので削除）
    df_hit = df_hit[(df_hit['語釈'] != '')]
    
    # ヒット数が多い場合は削除
    hit_count = len(df_hit)
    if hit_count > 10:
        df_hit = df_hit[0:10]
    
    # print
    if len(df_hit) > 0: print(df_hit)
    
    # 分割 /( で語釈を分割
    df_hit['語釈'] = df_hit['語釈'].str.split('/\(')
    df_hit['語釈'] = df_hit['語釈'].apply(lambda x: ['('+i for i in x if i != ''])  # 区切り文字が先頭なので先頭要素を除去（先頭以外を抽出）
    
    # 品詞を分割
    df_hit['語釈'] = df_hit['語釈'].apply(split品詞)

    print('--単語: ' + word + ' / ヒット数： ' + str(hit_count))
#    for k, s in enumerate(df_hit['語釈']):
#        print(str(k) +': ' + s[0][1])
    
    # 先頭の語釈を切り出し
    df_hit['先頭語釈'] = df_hit['語釈'].apply(lambda x: x[0][1])
    
    # ヒットなしの場合、空dfを準備
    if len(df_hit) == 0:
            df_hit = pd.DataFrame([[None,None]], columns=['見出し語','先頭語釈'])

    return df_hit[['見出し語','先頭語釈']].iloc[0]


def split品詞(wordlist):
    '''
    語釈（リスト）を品詞と語釈本文に分割（リスト内リストになる）
    '''
    # 複数語釈があるものは語釈 No.で区切る（1番目に No.が入っているか確認の条件もつけている）
    if len(wordlist) > 1 and re.search('\(\d+\)', wordlist[0]):
        for i, s in enumerate(wordlist):
            wordlist[i] = re.split('(.*?)\s\(\d+\)\s(.*)', s)
    # 単一語釈のものは閉じ括弧) +スペースで区切る
    else:
        wordlist[0] = re.split('(.*\))\s(.*)', wordlist[0])
    
    # 空文字要素を除去
    for i, s in enumerate(wordlist):
        wordlist[i] = [j for j in s if j != '']
        # s.remove('')は最初に該当しないものしか処理しないので不採用

    # print(wordlist)
        
    # 補正（先頭語釈のみ）： 語釈にカッコ書き（前後スペース）がある場合、品詞に語釈が入り込む（word: 経歴詐称）
    #                    品詞を再度　閉じかっこ+スペース+（始まりカッコ以外）で切り、切れた場合は後ろを語釈本文に入れる
    if len(wordlist[0]) > 1:
        temp = re.split('(.*\))\s([^\(].*)', wordlist[0][0])
        # 前後は空文字要素が切り出される（カウンタ*2）
        if len(temp) > 3:
            wordlist[0][0] = temp[1]
            wordlist[0][1] = temp[2] + ' ' + wordlist[0][1]

    # 補正：過剰な区切り（閉じ括弧で区切った結果品詞が無い＝品詞でない/( で切ってしまったもの）を繋ぎ直す
    for i, s in reversed(list(enumerate(wordlist))):
        for j, t in enumerate(s):
            # 品詞分割できてない（不正な区切りの後ろ側）を検知して、一つまえの語釈の後ろに'/'で結合（配列後ろから）
            if i > 0 and len(s) == 1:
                # 結合処理（当該語釈自体は削除）
                # print('i:' + str(i) + 'i,0:'+wordlist[i][0])
                if len(wordlist[i-1]) == 2:
                    wordlist[i-1][1] = wordlist[i-1][1] + '/' + t
                else:
                    wordlist[i-1][0] = wordlist[i-1][0] + '/' + t
                del(wordlist[i])

    # 補正：かっこ書きが複数ある場合、１つ目だけが分割されてしまうので補正
    for i, s in enumerate(wordlist):
        if len(s) > 1 and re.search('^(\(.*?\)\s)+', s[1]):
            # 一番後ろの閉じかっこで分割し、前半を品詞の後ろに結合。語釈は後半のみにする。
            # 前半のマッチングパターン：（ )+スペースのN回繰り返し。グループが入れ子なので2つに分割され、１つ目（外側）を採用
            word = re.split('(^(\(.*?\)\s)+)(.*)', s[1])
            s[0] = s[0] + ' ' + word[1]
            s[1] = word[3]

    # print(wordlist)
    return wordlist


def itemNameEnglish(sentence):
    '''
    項目名の英字化
    '''
    print('対象文字列： ' + sentence)
    # 形態素解析（mecab）
    # DataFrame化
    df = pd.DataFrame((mecab.parse(sentence)).splitlines())

    # タブ分割
    df = df[0].str.split(expand=True)

    # EOS行を除去
    df = df[~(df[0] == 'EOS')]

    # 英語付与
    df[['英訳見出し語','英訳先頭語釈']] = df[2].apply(search_dic)

    # ローマ字付与（英和辞書のヒット結果から。ヒットしない場合は原形(*)から。記号・助動詞は空文字化）
    #   (*)素形と原形が同じ場合はよみがなから。違う場合は原形から。素形がアルファベットの場合も原形から。(語：鬼滅の刃、100M背泳ぎのM)
    # df[['ローマ字訳']] = df['英訳見出し語'].apply(lambda x: str(conv.do(x)))  KeyErrorになる
    df['ローマ字訳'] = ''
    for i in range(len(df)):
        hinshi = df[3].iloc[i]  # 品詞で除外
        if '助動詞' in hinshi or '記号-一般' in hinshi or '記号-括弧' in hinshi :
            df['ローマ字訳'].iloc[i] = ''
        elif df['英訳見出し語'].iloc[i] != None :
            df['ローマ字訳'].iloc[i] = conv.do(df['英訳見出し語'].iloc[i])
        elif (df[0].iloc[i] != df[2].iloc[i]) or re.search(r'[a-zA-Z]+', df[0].iloc[i]):
            df['ローマ字訳'].iloc[i] = conv.do(df[2].iloc[i])
        else:
            df['ローマ字訳'].iloc[i] = conv.do(df[1].iloc[i])
    # 記号除去（mecabの品詞が記号ではないケースがあるためダメ押し）
    df['ローマ字訳'] = df['ローマ字訳'].apply(lambda x:  re.sub(re.compile("[!-/:-@[-`{-~]"), '', x))
    # 全角半角変換
    df['ローマ字訳'] = df['ローマ字訳'].apply(lambda x: x.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)})))

    # 強制変換単語を付与（強制変換にあたらない場合は空文字を設定
    df = df.merge(df_force[['日本語項目名','強制変換単語']], how='left',
                  left_on=0, right_on='日本語項目名').drop(['日本語項目名'], axis=1)
    df['強制変換単語'] = df['強制変換単語'].fillna('')
    
    # 英語・ローマ字の選択
    df['採用変換語'] = df.apply(translateLogic, axis=1)

    # ハイフン除去（スペース化）
    df['採用変換語'] = df['採用変換語'].str.replace('-',' ')
    
    print(df)

    # キャメルケース変換（先頭小文字）
#    result = ' '.join(df['採用変換語'].values.tolist()).title().replace(' ', '') #タイトルケースだと先頭数字の場合次の英字が大文字になってしまう
    result = ' '.join(df['採用変換語'].values.tolist())  #スペースで結合
    result = re.sub(r"\s+", " ", result)  #複数後のスペースを一つに
    result = re.sub(r' (.)',lambda m: m.group(1).upper(),result).replace(' ', '')  #スペース直後の1文字を大文字にして結合後、スペース除去
    result = result[0].lower() + result[1:]  #先頭１文字を小文字に
    #result = (result[0] if len(result) < 2 or result[1].isupper() else result[0].lower())  + result[1:] 
    print('変換結果: ' + result)
    
    return result


def translateLogic(row):
    '''
    英語・ローマ字の選択基準を実装
    引数 row: pandas.Series
    '''
    if row['英訳先頭語釈'] is not None:
        # 準備
        # 英語の最初の意味（スラッシュまたはかっこの前で切る）
        listE = re.split('[/(]', row['英訳先頭語釈'])
        # 閉じかっこを含む要素を除去(語：多数)
        listE = [j.strip() for j in listE if re.search('[/)]', j) == None]
        # 除去文字列の処理（ and, ',' ) をスペースに置換
        listE = [j.replace(' and ', ' ').replace(',', ' ') for j in listE]

        firstE = listE[0]
        #最初の意味が2単語以上で２つ目の意味がある場合、
        if len(firstE.split(' ')) > 1 and len(listE) > 1:
            # 2つ目の意味も見る
            secondE = listE[1]
            #  # 2つ目の意味に'.'がある場合、かっこで一つ目を補足説明しているケースなので１つ目を選択（何もしない）
            #  #if '.' not in secondE:
            # ２つ目の意味の方が単語数が少ない場合、2単語目を採用（一つ目を上書き）
            if len(secondE.split(' ')) < len(firstE.split(' ')):
                firstE = secondE
            # ２つ目の意味と単語数が同じ場合、文字数を比較して2単語目が少なければ採用（一つ目を上書き）
            if len(secondE.split(' ')) == len(firstE.split(' ')) and len(secondE) < len(firstE):
                firstE = secondE
        
    # （メイン）
    # 1.強制変換指定がある場合は優先
    if row['強制変換単語'] != '':
        answer = row['強制変換単語']
    # 2.助詞はローマ字
    elif '助詞' in row[3]:
        answer = row['ローマ字訳']
    # 3.英語がなし,ローマ字が空文字の場合も空文字
    elif row['英訳先頭語釈'] is None or row['ローマ字訳'] == '':
        answer = row['ローマ字訳']
    # 英語が3単語以上の場合ローマ字      
    elif len(firstE.split(' ')) > 2:
        answer = row['ローマ字訳']
    else:
        answer = firstE

    # print(answer)
    return answer


'''
コマンドライン実行時
    引数１番目：sys.argv[1] の内容により実行内容を制御
    1. 文字列（ピリオドなしで判定）の場合、引数の文字列を変換
    2. ファイル名（ピリオドで判定）の場合、ファイル内の1列目の文字列を変換し、2列目に更新
    （ファイル名は「項目一覧.csv」で固定し、同一フォルダ内に置くこと）
'''
if __name__ == '__main__':

    if '.' in sys.argv[1]:
        df_item = pd.read_csv(sys.argv[1])
        df_item['英語項目名'] = df_item['日本語項目名'].apply(itemNameEnglish)
        df_item.to_csv(sys.argv[1],index=False)
    else:
        itemNameEnglish(sys.argv[1])

