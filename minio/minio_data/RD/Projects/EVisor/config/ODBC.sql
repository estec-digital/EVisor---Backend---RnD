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
-- Orther case
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
    NULLIF(
      regexp_replace(
        regexp_replace(NULLIF(TRIM(%PART_SERI%), ''), '^https?://[^/]+/', ''),  -- loại bỏ http://.../
        '^' || COALESCE(
          (regexp_split_to_array(
             regexp_replace(NULLIF(TRIM(%PART_SERI%), ''), '^https?://[^/]+/', ''), '\+'
           ))[1],
          %PART_NO%
        ) || '\+?',  -- xóa phần part_no và dấu "+"
        ''
      ),
      ''
    ),
    %SERI_NO%
  ),
  NOW(),
  NOW()
);

---------------------
--- EXPORT
---------------------
INSERT INTO "WS_Export" ("project_code", "seri_number","MD","TEN_TU")
VALUES (
    %MA DU AN%,
    COALESCE(
    (regexp_split_to_array(
       regexp_replace(NULLIF(TRIM(%SERI_NO%), ''), '^https?://[^/]+/', ''),  -- loại bỏ http://.../
       '\+'
     ))[array_length(
       regexp_split_to_array(
         regexp_replace(NULLIF(TRIM(%SERI_NO%), ''), '^https?://[^/]+/', ''), '\+'
       ), 1
     )],
    %SERI_NO%
  )
);
-- Orther case
INSERT INTO "WS_Export" ("project_code", "seri_number", "MD", "TEN_TU")
VALUES (
  %MA DU AN%,
  COALESCE(
    NULLIF(
      regexp_replace(
        regexp_replace(NULLIF(TRIM(%SERI_NO%), ''), '^https?://[^/]+/', ''),  -- loại bỏ http://.../
        '^' || COALESCE(
          (regexp_split_to_array(
             regexp_replace(NULLIF(TRIM(%SERI_NO%), ''), '^https?://[^/]+/', ''), '\+'
           ))[1],
          ''
        ) || '\+?',  -- xóa phần đầu (mã hàng / part_no) và dấu "+"
        ''
      ),
      ''
    ),
    %SERI_NO%
  ),
  %MD%,
  %TEN_TU%
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


-- FUNCTION: public.ws_export_before_insert()

-- DROP FUNCTION IF EXISTS public.ws_export_before_insert();

CREATE OR REPLACE FUNCTION public.ws_export_before_insert()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
DECLARE
    existing_part_no_import text;
    existing_product_name text;
    existing_origin text;
BEGIN
    -- 1) Lấy part_no tương ứng với seri_number trong WS_Import (nếu có)
    SELECT part_no
    INTO existing_part_no_import
    FROM "WS_Import"
    WHERE seri_number = NEW.seri_number
    LIMIT 1;

    -- Nếu không tìm thấy part_no thì bỏ qua, trả NEW để UPDATE tiếp tục
    IF existing_part_no_import IS NULL THEN
        RETURN NEW;
    END IF;

    -- 2) Lấy thông tin product từ WS_Statistical theo part_no vừa tìm
    SELECT product_name, origin
    INTO existing_product_name, existing_origin
    FROM "WS_Statistical"
    WHERE part_no = existing_part_no_import
    LIMIT 1;

    -- 3) Nếu có dữ liệu ở WS_Statistical thì chèn 1 bản ghi vào WS_Export
    IF existing_part_no_import IS NOT NULL THEN
        WITH row_to_update AS (
		    SELECT id
		    FROM "WS_Installation"
		    WHERE part_no = existing_part_no_import
		      AND project_code = NEW.project_code
		      AND seri_number IS NULL
		    ORDER BY id
		    LIMIT 1
		)
		UPDATE "WS_Installation"
		SET seri_number = NEW.seri_number
		WHERE id IN (SELECT id FROM row_to_update);

        NEW.export_id := NULL;
		NEW.time := NOW();
		NEW.export_time := NOW();
        IF existing_product_name IS NOT NULL THEN
            NEW.product_name := existing_product_name;
        END IF;
		NEW.part_no := existing_part_no_import;
		IF existing_origin IS NOT NULL THEN
            NEW.origin := existing_origin;
        END IF;
		NEW.quantity := 1;
		NEW.cabinet := NULL;
		NEW.deleted := FALSE;
        RETURN NEW;
    END IF;

    RETURN NEW;
END;
$BODY$;

ALTER FUNCTION public.ws_export_before_insert()
    OWNER TO evisor;
