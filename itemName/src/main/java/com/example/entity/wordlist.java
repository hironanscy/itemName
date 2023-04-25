package com.example.entity;

import java.io.Serializable;

import javax.validation.constraints.NotNull;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;

@Schema(description = "日本語項目名と英語項目名のペア（要求時は日本語のみ必須）")
@Data
@AllArgsConstructor
public class wordlist implements Serializable {
    private static final long serialVersionUID = 1L;

    @NotNull
    @Schema(description = "日本語項目名", example = "顧客氏名")
    private String japanese;

    @Schema(description = "英語項目名", example = "customerName")
    private String english;
}
