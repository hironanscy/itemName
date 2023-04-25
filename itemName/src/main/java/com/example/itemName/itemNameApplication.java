package com.example.itemName;

import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;

import com.example.entity.wordlist;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.RestController;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;

@SpringBootApplication
@RestController
public class itemNameApplication {

	@Value("${filepath}")
	private String filepath;

	public static void main(String[] args) {
		SpringApplication.run(itemNameApplication.class, args);
	}

	@Operation(summary = "英語項目名変換", responses = {
			@ApiResponse(description = "Successful Operation", responseCode = "200", content = @Content(mediaType = "application/json", schema = @Schema(implementation = wordlist.class))),
			@ApiResponse(responseCode = "500", description = "Server error (main search proccess failed)", content = @Content) })
	@PostMapping("/v1/")
	@ResponseBody
	public List<wordlist> itemNameEnglish(@RequestBody List<wordlist> inList) {

		pycaller pycaller = new pycaller(filepath);

		// タイムスタンプと拡張子付与
		final String filename = filepath + "/python/data/wordSearchList_"
				+ (new SimpleDateFormat("MMdd_HHmmss_SSS")).format(new Date()) + ".csv";
		pycaller.writeCSV(inList, filename);

		String retStr = "";
		try {
			retStr = pycaller.runpy(new String[] { filename });
		} catch (IOException e) {
			e.printStackTrace(System.out);
		}
		// return "Hello! py " + retStr;
		if (retStr.charAt(0) == '0') {
			return pycaller.readCSV(filename);
		} else {
			throw new RuntimeException(retStr.substring(2));
		}
	}

}
