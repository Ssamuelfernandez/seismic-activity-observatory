-- [1] caso1_faq12: cuarentena por motivo (SQL)
SELECT reason, count(*) FROM live.quarantine GROUP BY reason ORDER BY reason;

-- [2] caso2_faq12_latitud145_x2: cuarentena por motivo (SQL)
SELECT reason, count(*) FROM live.quarantine GROUP BY reason ORDER BY reason;

-- [3] caso3_faq12_dmin_nan_x2: cuarentena por motivo (SQL)
SELECT reason, count(*) FROM live.quarantine GROUP BY reason ORDER BY reason;

