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
