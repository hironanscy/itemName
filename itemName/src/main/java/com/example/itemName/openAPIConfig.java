package com.example.itemName;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.swagger.v3.oas.models.ExternalDocumentation;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;

@Configuration
public class openAPIConfig {

    @Bean
    public OpenAPI itemNameOpenAPI() {
        return new OpenAPI().info(new Info().title("英語項目名変換API").description(
                "日本語項目名を英語に変換    powered by : mecab(形態素解析), kakasi(ローマ字変換)  impl: python(main search),spring boot")
                .version("v0.0.1").license(new License().name("springdoc-openapi").url("https://springdoc.org/")))
                .externalDocs(new ExternalDocumentation().description(
                        "dictionary: EDICT(free Eng.-Jap.dictionary data(link)), mecab-ipadic-neologd, HELIOS単語一覧(CS/UC), HELIOS-API英単語一覧(OC)")
                        .url("https://www.edrdg.org/jmdict/edict.html"));
    }
}
