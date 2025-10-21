---------------------
--- IMPORT
---------------------
INSERT INTO "WS_Import" ("import_id", "project_code", "part_no", "seri_number", "time", "import_time")
VALUES (
  %PO%,
  %MA DU AN%,
  COALESCE(
    (regexp_split_to_array(
       regexp_replace(NULLIF(TRIM(%PART_SERI%), ''), '^https?://[^/]+/', ''),  -- loại bỏ http://.../
       '\+'
     ))[1],
    %PART_NO%
  ),
  COALESCE(
    (regexp_split_to_array(
       regexp_replace(NULLIF(TRIM(%PART_SERI%), ''), '^https?://[^/]+/', ''),  -- loại bỏ http://.../
       '\+'
     ))[array_length(
       regexp_split_to_array(
         regexp_replace(NULLIF(TRIM(%PART_SERI%), ''), '^https?://[^/]+/', ''), '\+'
       ), 1
     )],
    %SERI_NO%
  ),
  NOW(),
  NOW()
);
---------------------
--- EXPORT
---------------------
INSERT INTO "WS_Export" ("export_id", "project_code", "part_no", "seri_number", "time", "export_time")
VALUES (
  %PO%,
  %MA DU AN%,
  COALESCE(
    (regexp_split_to_array(
       regexp_replace(NULLIF(TRIM(%PART_SERI%), ''), '^https?://[^/]+/', ''),  -- loại bỏ http://.../
       '\+'
     ))[1],
    %PART_NO%
  ),
  COALESCE(
    (regexp_split_to_array(
       regexp_replace(NULLIF(TRIM(%PART_SERI%), ''), '^https?://[^/]+/', ''),  -- loại bỏ http://.../
       '\+'
     ))[array_length(
       regexp_split_to_array(
         regexp_replace(NULLIF(TRIM(%PART_SERI%), ''), '^https?://[^/]+/', ''), '\+'
       ), 1
     )],
    %SERI_NO%
  ),
  NOW(),
  NOW()
);


---------------------
--- TRIGGER
---------------------
-- FUNCTION: public.ws_import_upsert()

-- DROP FUNCTION IF EXISTS public.ws_import_upsert();

CREATE OR REPLACE FUNCTION public.ws_import_upsert()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
DECLARE
    existing_id varchar;
    existing_product_name varchar;
    existing_origin varchar;
	existing_part_no varchar;
    existing_seri_number varchar;
    existing_project_code varchar;
BEGIN
    -- Kiểm tra bản ghi trùng để tăng quantity
    SELECT import_id, part_no, seri_number, project_code
    INTO existing_id, existing_part_no, existing_seri_number, existing_project_code
    FROM "WS_Import"
    WHERE part_no = NEW.part_no
      AND seri_number = NEW.seri_number
      AND project_code = NEW.project_code
      AND import_id = NEW.import_id::varchar
    LIMIT 1
	FOR UPDATE;

    -- Lấy product_name và origin dựa trên part_no nếu có
    SELECT product_name, origin
    INTO existing_product_name, existing_origin
    FROM "WS_Import"
    WHERE part_no = NEW.part_no
    LIMIT 1;

    IF existing_id IS NOT NULL THEN
        -- Nếu trùng -> tăng quantity
        UPDATE "WS_Import"
        SET quantity = COALESCE(quantity, 0) + 1
        WHERE import_id = existing_id
			AND part_no = existing_part_no
			AND seri_number = existing_seri_number
			AND project_code = existing_project_code;
        RETURN NULL; -- hủy insert gốc
    ELSE
        -- Nếu chưa có -> insert mới với quantity = 1
        NEW.quantity := 1;

        -- Gán product_name và origin từ bản ghi cùng part_no nếu có
        IF existing_product_name IS NOT NULL THEN
            NEW.product_name := existing_product_name;
        END IF;

        IF existing_origin IS NOT NULL THEN
            NEW.origin := existing_origin;
        END IF;

        RETURN NEW;
    END IF;
END;
$BODY$;

ALTER FUNCTION public.ws_import_upsert()
    OWNER TO evisor;
