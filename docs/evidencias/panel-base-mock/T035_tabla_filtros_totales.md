| Filtros | Parámetros enviados (buildRequest) | metadata.total (eventos) | stats.total | count | truncated | null_mag_excluded (hist magnitud no_value) | Coincide |
|---|---|---|---|---|---|---|---|
| 1 h | `{"mode":"live","start":"2026-11-10T18:18:45.420Z"}` | 9 | 9 | 9 | false | 0 (hist: 0) | OK |
| 24 h | `{"mode":"live","start":"2026-11-09T19:18:45.420Z"}` | 206 | 206 | 206 | false | 0 (hist: 0) | OK |
| 7 d | `{"mode":"live","start":"2026-11-03T19:18:45.420Z"}` | 1280 | 1280 | 1280 | false | 0 (hist: 0) | OK |
| 30 d | `{"mode":"live","start":"2026-10-11T19:18:45.420Z"}` | 1280 | 1280 | 1280 | false | 0 (hist: 0) | OK |
| 1 año | `{"mode":"live","start":"2025-11-10T19:18:45.420Z"}` | 3333 | 3333 | 3333 | false | 0 (hist: 0) | OK |
| rango 2026-10-31..2026-11-02 | `{"mode":"live","start":"2026-10-31T00:00:00.000Z","end":"2026-11-03T00:00:00.000Z"}` | 0 | 0 | 0 | false | 0 (hist: 0) | OK |
| rango 2026-11-05..2026-11-07 | `{"mode":"live","start":"2026-11-05T00:00:00.000Z","end":"2026-11-08T00:00:00.000Z"}` | 529 | 529 | 529 | false | 0 (hist: 0) | OK |
| 24 h, min_mag 0 | `{"mode":"live","start":"2026-11-09T19:18:45.420Z"}` | 206 | 206 | 206 | false | 0 (hist: 0) | OK |
| 24 h, min_mag 2 | `{"mode":"live","min_mag":2,"start":"2026-11-09T19:18:45.420Z"}` | 75 | 75 | 75 | false | 0 (hist: 0) | OK |
| 24 h, min_mag 4 | `{"mode":"live","min_mag":4,"start":"2026-11-09T19:18:45.420Z"}` | 21 | 21 | 21 | false | 0 (hist: 0) | OK |
| 7 d, min_mag 4 | `{"mode":"live","min_mag":4,"start":"2026-11-03T19:18:45.420Z"}` | 110 | 110 | 110 | false | 0 (hist: 0) | OK |
| 24 h, country USA | `{"mode":"live","country_id":"USA","start":"2026-11-09T19:18:45.420Z"}` | 159 | 159 | 159 | false | 0 (hist: 0) | OK |
| 24 h, country none | `{"mode":"live","country_id":"none","start":"2026-11-09T19:18:45.420Z"}` | 37 | 37 | 37 | false | 0 (hist: 0) | OK |
| 24 h, country ZZZ (inexistente) | `{"mode":"live","country_id":"ZZZ","start":"2026-11-09T19:18:45.420Z"}` | 0 | 0 | 0 | false | 0 (hist: 0) | OK |
| 7 d, USA, min_mag 2 | `{"mode":"live","min_mag":2,"country_id":"USA","start":"2026-11-03T19:18:45.420Z"}` | 143 | 143 | 143 | false | 0 (hist: 0) | OK |
| 30 d (límite de truncado: limit=50) | `{"mode":"live","start":"2026-10-11T19:18:45.420Z"}` | 1280 | 1280 | 50 | true | 0 (hist: 0) | OK |

comparison (24 h, sin filtros): {"unit":"events","min_mag_applied":4,"recent_period":{"start":1794251925989,"end":1794338325989},"reference_period":{"start":1735689600000,"end":1767225600000},"n_recent":21,"n_2025":18302,"daily_mean_2025":50.14246575342466,"diff_abs":-29.14246575342466,"variation_pct":-58.12,"recent_incomplete":true}
comparison con min_mag=0: min_mag_applied=4 n_recent=21 n_2025=18302 variation_pct=-58.12
comparison con min_mag=2: min_mag_applied=4 n_recent=21 n_2025=18302 variation_pct=-58.12
comparison con min_mag=4: min_mag_applied=4 n_recent=21 n_2025=18302 variation_pct=-58.12
comparison con min_mag=5: min_mag_applied=5 n_recent=7 n_2025=2129 variation_pct=20.01
replay request={"mode":"replay","start":"2025-01-01T00:00:00.000Z","end":"2026-01-01T00:00:00.000Z"}
replay eventos: metadata={"generated":1794338326052,"last_ingestion":1794338297030,"mode":"replay","count":0,"total":0,"truncated":false,"next_cursor":null,"null_mag_excluded":0} features=0
replay stats: metadata={"generated":1794338326061,"last_ingestion":1794338297030,"mode":"replay"} total=0 comparison=null by_hour=8760 buckets
deriveDataState(replay features=0, sin error) = empty
