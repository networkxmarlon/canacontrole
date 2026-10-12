CREATE TABLE ftc_colheitas (
    id VARCHAR2(36 CHAR) CONSTRAINT ftc_colheitas_pk PRIMARY KEY,
    talhao VARCHAR2(60 CHAR) NOT NULL,
    data_colheita DATE NOT NULL,
    area_ha NUMBER(14,4) NOT NULL,
    colhida_t NUMBER(18,4) NOT NULL,
    amostra_m2 NUMBER(12,4) NOT NULL,
    perda_kg NUMBER(14,4) NOT NULL,
    preco_t NUMBER(14,2) NOT NULL,
    origem VARCHAR2(12 CHAR) NOT NULL,
    observacao VARCHAR2(240 CHAR),
    CONSTRAINT ftc_colheitas_uq UNIQUE (talhao, data_colheita),
    CONSTRAINT ftc_area_ck CHECK (area_ha > 0 AND area_ha <= 100000),
    CONSTRAINT ftc_colhida_ck CHECK (colhida_t >= 0 AND colhida_t <= 100000000),
    CONSTRAINT ftc_amostra_ck CHECK
        (amostra_m2 > 0 AND amostra_m2 <= 100000 AND amostra_m2 <= area_ha * 10000),
    CONSTRAINT ftc_perda_ck CHECK (perda_kg >= 0 AND perda_kg <= 1000000),
    CONSTRAINT ftc_preco_ck CHECK (preco_t >= 0 AND preco_t <= 1000000),
    CONSTRAINT ftc_origem_ck CHECK (origem IN ('observado', 'sintetico')),
    CONSTRAINT ftc_massa_ck CHECK (colhida_t > 0 OR perda_kg > 0)
);
