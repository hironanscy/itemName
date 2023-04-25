package com.example.itemName;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.List;

import com.example.entity.wordlist;

import lombok.AllArgsConstructor;

@AllArgsConstructor
public class pycaller {

    private String filepath;

    public String runpy(String[] args) throws IOException {
        Runtime runtime = Runtime.getRuntime();

        // String[] Command = { "/usr/bin/bash", "-c", "pwd" }; // cmd.exeでpythonを起動
        // String[] Command = { "/usr/bin/bash", "-c", "python3
        // /home/nagaisi/python/blankfunc.py 'blank func'" }; // cmd.exeでpythonを起動
        String[] Command = { "/bin/sh", "-c", "cd " + filepath + "/python; python3 itemNameEnglish.py '" + args[0] + "'" }; // pythonフォルダで、cmd.exeでpythonを起動

        Process p = null;
        try {
            p = runtime.exec(Command); // Commandを実行する
        } catch (IOException e) {
            e.printStackTrace();
        }

        try {
            p.waitFor(); // プロセスの正常終了まで待機させる
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        InputStream is = null;
        if (p.exitValue() == 0) {
            is = p.getInputStream(); // プロセスの結果を変数に格納する
        } else {
            is = p.getErrorStream(); // プロセスの結果を変数に格納する
        }
        BufferedReader br = new BufferedReader(new InputStreamReader(is)); // テキスト読み込みを行えるようにする

        String line = "";
        String lastLine = "";
        while (true) {
            line = br.readLine();
            if (line == null) {
                break; // 全ての行を読み切ったら抜ける
            } else {
                System.out.println("[itemName-py] " + line); // 実行結果を表示
                lastLine = line;
            }
        }
        return p.exitValue() + " " + lastLine; // EXITコード+最終行を返却
    }

    public List<wordlist> readCSV(String filename) {

        List<wordlist> retlist = new ArrayList<>();
        try {
            File csv = new File(filename); // CSVデータファイル

            BufferedReader br = new BufferedReader(new FileReader(csv));

            // 最終行まで読み込む
            String line = "";
            while ((line = br.readLine()) != null) {

                // 1行をデータの要素に分割
                String[] data = line.split(",");
                retlist.add(new wordlist(data[0], data[1]));
            }
            br.close();

            // ヘッダー削除
            if (retlist.get(0).getJapanese().equals("日本語項目名")) {
                retlist.remove(0);
            }

        } catch (FileNotFoundException e) {
            // Fileオブジェクト生成時の例外捕捉
            e.printStackTrace();
        } catch (IOException e) {
            // BufferedReaderオブジェクトのクローズ時の例外捕捉
            e.printStackTrace();
        }

        return retlist;
    }

    public void writeCSV(List<wordlist> word, String filename) {

        try {
            File csv = new File(filename); // CSVデータファイル
            // 追記モード
            BufferedWriter bw = new BufferedWriter(new FileWriter(csv, false));
            // ヘッダー出力
            bw.write("日本語項目名,英語項目名");
            bw.newLine();
            // データ行の追加
            word.forEach(s -> {
                // ラムダの中で例外をcatchする
                try {
                    bw.write(s.getJapanese() + "," + s.getEnglish());
                    bw.newLine();
                } catch (IOException ex) {
                    ex.printStackTrace(System.out);
                    throw new UncheckedIOException(ex);
                }
            });
            bw.close();

        } catch (FileNotFoundException e) {
            // Fileオブジェクト生成時の例外捕捉
            e.printStackTrace();
        } catch (IOException e) {
            // BufferedWriterオブジェクトのクローズ時の例外捕捉
            e.printStackTrace();
        }
        return;
    }

}