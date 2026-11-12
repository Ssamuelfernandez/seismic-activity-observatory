# Tablas de mediciones (SINTÉTICO)

Todas las cifras provienen de datos SINTÉTICO (`bench`, semilla 20251113) salvo lo que se indique como REAL. Tiempos en milisegundos (base decimal, `time.perf_counter`), memoria en KiB (base 1024, `tracemalloc`), calentamiento descartado. Las consultas se miden desde el cliente (ida y vuelta incluidas) y el tiempo del servidor sale del plan `EXPLAIN ANALYZE`.

Parámetros: tamaños [1000, 10000, 100000], repeticiones máximas 15, presupuesto 90 s por serie. N real puede ser menor que la pedida por el presupuesto.

## Operación a: búsqueda por id (SINTÉTICO)

| Id | Estrategia | Tamaño | Caso | N real (pedida) | Mediana (ms) | Q1-Q3 (ms) | IQR (ms) | Mín-Máx (ms) | Pico (KiB) | Servidor (ms) | Nodo del plan | Notas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| search.dict.1000.absent | dict | 1000 | absent | 15 (15) | 0.000062 | 0.000062-0.000083 | 0.000021 | 0.000062-0.000176 | no aplica | no aplica | no aplica | no aplica |
| search.dict.1000.first | dict | 1000 | first | 15 (15) | 0.000062 | 0.000062-0.000072 | 0.000010 | 0.000061-0.000340 | no aplica | no aplica | no aplica | no aplica |
| search.dict.1000.last | dict | 1000 | last | 15 (15) | 0.000062 | 0.000062-0.000072 | 0.000010 | 0.000062-0.000083 | no aplica | no aplica | no aplica | no aplica |
| search.dict.1000.middle | dict | 1000 | middle | 15 (15) | 0.000072 | 0.000072-0.000078 | 0.000006 | 0.000072-0.000134 | no aplica | no aplica | no aplica | no aplica |
| search.dict_build.1000.build | dict_build | 1000 | build | 15 (15) | 0.024549 | 0.024487-0.024611 | 0.000124 | 0.024404-0.027347 | 38.1 | no aplica | no aplica | no aplica |
| search.list.1000.absent | list | 1000 | absent | 15 (15) | 0.011748 | 0.011737-0.012439 | 0.000702 | 0.011666-0.072905 | no aplica | no aplica | no aplica | no aplica |
| search.list.1000.first | list | 1000 | first | 15 (15) | 0.000103 | 0.000093-0.000124 | 0.000031 | 0.000093-0.001208 | no aplica | no aplica | no aplica | no aplica |
| search.list.1000.last | list | 1000 | last | 15 (15) | 0.011748 | 0.011727-0.011779 | 0.000052 | 0.011706-0.011841 | no aplica | no aplica | no aplica | no aplica |
| search.list.1000.middle | list | 1000 | middle | 15 (15) | 0.006390 | 0.006370-0.006400 | 0.000031 | 0.006359-0.006514 | no aplica | no aplica | no aplica | no aplica |
| search.pg_index.1000.absent | pg_index | 1000 | absent | 15 (15) | 0.154016 | 0.149654-0.161438 | 0.011784 | 0.141896-0.170455 | no aplica | 0.010000 | Index Scan | no aplica |
| search.pg_index.1000.first | pg_index | 1000 | first | 15 (15) | 0.156845 | 0.156308-0.160075 | 0.003767 | 0.155399-0.177946 | no aplica | 0.011000 | Index Scan | no aplica |
| search.pg_index.1000.last | pg_index | 1000 | last | 15 (15) | 0.157866 | 0.155657-0.169945 | 0.014288 | 0.155306-0.183489 | no aplica | 0.013000 | Index Scan | no aplica |
| search.pg_index.1000.middle | pg_index | 1000 | middle | 15 (15) | 0.155182 | 0.154872-0.156328 | 0.001455 | 0.153964-0.193978 | no aplica | 0.012000 | Index Scan | no aplica |
| search.pg_seq.1000.absent | pg_seq | 1000 | absent | 15 (15) | 0.169676 | 0.169041-0.170544 | 0.001502 | 0.168799-0.332096 | no aplica | 0.033000 | Seq Scan | no aplica |
| search.pg_seq.1000.first | pg_seq | 1000 | first | 15 (15) | 0.148111 | 0.147476-0.167153 | 0.019677 | 0.146924-0.180341 | no aplica | 0.036000 | Seq Scan | no aplica |
| search.pg_seq.1000.last | pg_seq | 1000 | last | 15 (15) | 0.179484 | 0.178234-0.184939 | 0.006705 | 0.176810-0.194463 | no aplica | 0.036000 | Seq Scan | no aplica |
| search.pg_seq.1000.middle | pg_seq | 1000 | middle | 15 (15) | 0.168922 | 0.166884-0.171529 | 0.004645 | 0.165588-0.194566 | no aplica | 0.038000 | Seq Scan | no aplica |
| search.dict.10000.absent | dict | 10000 | absent | 15 (15) | 0.000072 | 0.000062-0.000083 | 0.000021 | 0.000062-0.000165 | no aplica | no aplica | no aplica | no aplica |
| search.dict.10000.first | dict | 10000 | first | 15 (15) | 0.000072 | 0.000072-0.000073 | 0.000001 | 0.000062-0.000134 | no aplica | no aplica | no aplica | no aplica |
| search.dict.10000.last | dict | 10000 | last | 15 (15) | 0.000072 | 0.000072-0.000073 | 0.000001 | 0.000062-0.000124 | no aplica | no aplica | no aplica | no aplica |
| search.dict.10000.middle | dict | 10000 | middle | 15 (15) | 0.000072 | 0.000072-0.000073 | 0.000001 | 0.000062-0.000083 | no aplica | no aplica | no aplica | no aplica |
| search.dict_build.10000.build | dict_build | 10000 | build | 15 (15) | 0.301899 | 0.297233-0.312249 | 0.015015 | 0.295210-0.337824 | 304.1 | no aplica | no aplica | no aplica |
| search.list.10000.absent | list | 10000 | absent | 15 (15) | 0.125709 | 0.124687-0.127515 | 0.002828 | 0.123933-0.193028 | no aplica | no aplica | no aplica | no aplica |
| search.list.10000.first | list | 10000 | first | 15 (15) | 0.000113 | 0.000104-0.000124 | 0.000020 | 0.000103-0.000341 | no aplica | no aplica | no aplica | no aplica |
| search.list.10000.last | list | 10000 | last | 15 (15) | 0.125543 | 0.124681-0.133312 | 0.008631 | 0.124160-0.152967 | no aplica | no aplica | no aplica | no aplica |
| search.list.10000.middle | list | 10000 | middle | 15 (15) | 0.064047 | 0.062426-0.071165 | 0.008739 | 0.061631-0.165196 | no aplica | no aplica | no aplica | no aplica |
| search.pg_index.10000.absent | pg_index | 10000 | absent | 15 (15) | 0.147244 | 0.145990-0.158558 | 0.012569 | 0.144549-0.205684 | no aplica | 0.011000 | Index Scan | no aplica |
| search.pg_index.10000.first | pg_index | 10000 | first | 15 (15) | 0.159404 | 0.158496-0.163792 | 0.005296 | 0.157794-0.182746 | no aplica | 0.012000 | Index Scan | no aplica |
| search.pg_index.10000.last | pg_index | 10000 | last | 15 (15) | 0.160251 | 0.159441-0.160927 | 0.001486 | 0.158909-0.164834 | no aplica | 0.012000 | Index Scan | no aplica |
| search.pg_index.10000.middle | pg_index | 10000 | middle | 15 (15) | 0.159941 | 0.159069-0.161918 | 0.002849 | 0.157184-0.200012 | no aplica | 0.012000 | Index Scan | no aplica |
| search.pg_seq.10000.absent | pg_seq | 10000 | absent | 15 (15) | 0.445746 | 0.426178-0.450332 | 0.024155 | 0.423963-0.490312 | no aplica | 0.462000 | Seq Scan | no aplica |
| search.pg_seq.10000.first | pg_seq | 10000 | first | 15 (15) | 0.162367 | 0.157020-0.182436 | 0.025416 | 0.156297-0.217520 | no aplica | 0.437000 | Seq Scan | no aplica |
| search.pg_seq.10000.last | pg_seq | 10000 | last | 15 (15) | 0.437239 | 0.435645-0.441436 | 0.005792 | 0.431572-0.453334 | no aplica | 0.316000 | Seq Scan | no aplica |
| search.pg_seq.10000.middle | pg_seq | 10000 | middle | 15 (15) | 0.320151 | 0.313477-0.352474 | 0.038997 | 0.307463-0.395553 | no aplica | 0.413000 | Seq Scan | no aplica |
| search.dict.100000.absent | dict | 100000 | absent | 15 (15) | 0.000062 | 0.000062-0.000072 | 0.000010 | 0.000061-0.000361 | no aplica | no aplica | no aplica | no aplica |
| search.dict.100000.first | dict | 100000 | first | 15 (15) | 0.000062 | 0.000062-0.000072 | 0.000010 | 0.000062-0.000113 | no aplica | no aplica | no aplica | no aplica |
| search.dict.100000.last | dict | 100000 | last | 15 (15) | 0.000072 | 0.000062-0.000072 | 0.000010 | 0.000062-0.000082 | no aplica | no aplica | no aplica | no aplica |
| search.dict.100000.middle | dict | 100000 | middle | 15 (15) | 0.000072 | 0.000072-0.000073 | 0.000001 | 0.000062-0.000113 | no aplica | no aplica | no aplica | no aplica |
| search.dict_build.100000.build | dict_build | 100000 | build | 15 (15) | 6.513 | 6.308-6.832 | 0.523769 | 6.143-7.920 | 5632.1 | no aplica | no aplica | no aplica |
| search.list.100000.absent | list | 100000 | absent | 15 (15) | 2.059 | 1.983-2.173 | 0.189433 | 1.956-2.376 | no aplica | no aplica | no aplica | no aplica |
| search.list.100000.first | list | 100000 | first | 15 (15) | 0.000104 | 0.000103-0.000124 | 0.000021 | 0.000103-0.000300 | no aplica | no aplica | no aplica | no aplica |
| search.list.100000.last | list | 100000 | last | 15 (15) | 2.022 | 2.002-2.080 | 0.077268 | 1.958-2.291 | no aplica | no aplica | no aplica | no aplica |
| search.list.100000.middle | list | 100000 | middle | 15 (15) | 0.843322 | 0.838098-0.891783 | 0.053685 | 0.824565-1.172 | no aplica | no aplica | no aplica | no aplica |
| search.pg_index.100000.absent | pg_index | 100000 | absent | 15 (15) | 0.146670 | 0.145735-0.160516 | 0.014781 | 0.144957-0.177773 | no aplica | 0.011000 | Index Scan | no aplica |
| search.pg_index.100000.first | pg_index | 100000 | first | 15 (15) | 0.157334 | 0.156998-0.158273 | 0.001275 | 0.156146-0.177010 | no aplica | 0.013000 | Index Scan | no aplica |
| search.pg_index.100000.last | pg_index | 100000 | last | 15 (15) | 0.163920 | 0.160699-0.180827 | 0.020128 | 0.158583-0.197438 | no aplica | 0.013000 | Index Scan | no aplica |
| search.pg_index.100000.middle | pg_index | 100000 | middle | 15 (15) | 0.157592 | 0.156967-0.162495 | 0.005528 | 0.152595-0.414276 | no aplica | 0.013000 | Index Scan | no aplica |
| search.pg_seq.100000.absent | pg_seq | 100000 | absent | 15 (15) | 4.799 | 4.487-5.296 | 0.809351 | 4.036-6.692 | no aplica | 4.539 | Seq Scan | no aplica |
| search.pg_seq.100000.first | pg_seq | 100000 | first | 15 (15) | 0.175688 | 0.164616-0.187256 | 0.022639 | 0.152678-0.334746 | no aplica | 7.057 | Seq Scan | no aplica |
| search.pg_seq.100000.last | pg_seq | 100000 | last | 15 (15) | 4.096 | 3.939-4.554 | 0.614459 | 3.630-5.224 | no aplica | 4.681 | Seq Scan | no aplica |
| search.pg_seq.100000.middle | pg_seq | 100000 | middle | 15 (15) | 2.332 | 2.104-2.597 | 0.492709 | 1.753-3.431 | no aplica | 4.805 | Seq Scan | no aplica |

## Operación b: integración geográfica (SINTÉTICO)

| Id | Estrategia | Tamaño | Caso | N real (pedida) | Mediana (ms) | Q1-Q3 (ms) | IQR (ms) | Mín-Máx (ms) | Pico (KiB) | Servidor (ms) | Nodo del plan | Notas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| geo.naive.1000.mixed | naive | 1000 | mixed | 15 (15) | 19.145 | 18.999-19.223 | 0.223426 | 18.877-20.035 | 9.4 | no aplica | no aplica | puntos con resultado distinto entre métodos: 0 de 1000 |
| geo.naive.1000.ocean | naive | 1000 | ocean | 15 (15) | 21.133 | 21.037-21.263 | 0.226342 | 20.686-22.011 | 9.4 | no aplica | no aplica | puntos con resultado distinto entre métodos: 0 de 1000 |
| geo.strtree.1000.mixed | strtree | 1000 | mixed | 15 (15) | 5.857 | 5.713-5.999 | 0.286389 | 5.667-6.196 | 9.6 | no aplica | no aplica | puntos con resultado distinto entre métodos: 0 de 1000 |
| geo.strtree.1000.ocean | strtree | 1000 | ocean | 15 (15) | 5.629 | 5.592-5.694 | 0.102197 | 5.511-6.111 | 9.6 | no aplica | no aplica | puntos con resultado distinto entre métodos: 0 de 1000 |
| geo.strtree_build.1000.build | strtree_build | 1000 | build | 15 (15) | 0.019130 | 0.019062-0.019388 | 0.000325 | 0.018882-0.025850 | 4.8 | no aplica | no aplica | no aplica |
| geo.naive.10000.mixed | naive | 10000 | mixed | 15 (15) | 194.085 | 191.381-196.100 | 4.719 | 189.457-206.551 | 84.0 | no aplica | no aplica | puntos con resultado distinto entre métodos: 0 de 10000 |
| geo.naive.10000.ocean | naive | 10000 | ocean | 15 (15) | 212.973 | 211.492-213.488 | 1.996 | 207.959-217.201 | 84.0 | no aplica | no aplica | puntos con resultado distinto entre métodos: 0 de 10000 |
| geo.strtree.10000.mixed | strtree | 10000 | mixed | 15 (15) | 59.818 | 59.148-60.652 | 1.504 | 57.808-61.560 | 84.1 | no aplica | no aplica | puntos con resultado distinto entre métodos: 0 de 10000 |
| geo.strtree.10000.ocean | strtree | 10000 | ocean | 15 (15) | 54.408 | 53.842-56.197 | 2.355 | 53.477-57.919 | 84.1 | no aplica | no aplica | puntos con resultado distinto entre métodos: 0 de 10000 |
| geo.strtree_build.10000.build | strtree_build | 10000 | build | 15 (15) | 0.019016 | 0.018881-0.019315 | 0.000434 | 0.018820-0.026748 | 4.7 | no aplica | no aplica | no aplica |
| geo.naive.100000.mixed | naive | 100000 | mixed | 15 (15) | 1919.620 | 1905.699-1935.415 | 29.716 | 1893.087-1968.938 | 783.0 | no aplica | no aplica | puntos con resultado distinto entre métodos: 0 de 100000 |
| geo.naive.100000.ocean | naive | 100000 | ocean | 15 (15) | 2130.540 | 2109.882-2148.102 | 38.220 | 2095.417-2236.044 | 783.0 | no aplica | no aplica | puntos con resultado distinto entre métodos: 0 de 100000 |
| geo.strtree.100000.mixed | strtree | 100000 | mixed | 15 (15) | 610.288 | 606.003-617.694 | 11.691 | 587.925-624.790 | 783.2 | no aplica | no aplica | puntos con resultado distinto entre métodos: 0 de 100000 |
| geo.strtree.100000.ocean | strtree | 100000 | ocean | 15 (15) | 568.380 | 561.913-595.491 | 33.578 | 540.254-647.124 | 783.1 | no aplica | no aplica | puntos con resultado distinto entre métodos: 0 de 100000 |
| geo.strtree_build.100000.build | strtree_build | 100000 | build | 15 (15) | 0.018994 | 0.018932-0.019335 | 0.000403 | 0.018767-0.027242 | 4.7 | no aplica | no aplica | no aplica |

## Operación c y E6: agregaciones Q4, Q3 y Q2 sin y con índice (SINTÉTICO)

| Id | Estrategia | Tamaño | Caso | N real (pedida) | Mediana (ms) | Q1-Q3 (ms) | IQR (ms) | Mín-Máx (ms) | Pico (KiB) | Servidor (ms) | Nodo del plan | Notas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agg.q2_country_index.1000.month | q2_country_index | 1000 | month | 15 (15) | 0.155059 | 0.153970-0.156431 | 0.002462 | 0.152911-0.206262 | no aplica | 0.016000 | Aggregate, Index Only Scan | selectividad 0.0050 |
| agg.q2_country_index.1000.range | q2_country_index | 1000 | range | 15 (15) | 0.157401 | 0.157195-0.161557 | 0.004362 | 0.155295-0.183778 | no aplica | 0.024000 | Aggregate, Bitmap Heap Scan | selectividad 0.0200 |
| agg.q2_noindex.1000.month | q2_noindex | 1000 | month | 15 (15) | 0.200038 | 0.198478-0.226022 | 0.027543 | 0.197457-0.242807 | no aplica | 0.058000 | Aggregate, Seq Scan | selectividad 0.0050 |
| agg.q2_noindex.1000.range | q2_noindex | 1000 | range | 15 (15) | 0.218548 | 0.203192-0.229807 | 0.026616 | 0.202174-0.280168 | no aplica | 0.061000 | Aggregate, Seq Scan | selectividad 0.0200 |
| agg.q3_mag_index.1000.mag4 | q3_mag_index | 1000 | mag4 | 15 (15) | 0.203145 | 0.201359-0.209179 | 0.007820 | 0.199305-0.298621 | no aplica | 0.096000 | Aggregate, Seq Scan | selectividad 1.0000 |
| agg.q3_mag_index.1000.p99 | q3_mag_index | 1000 | p99 | 15 (15) | 0.196517 | 0.194143-0.204218 | 0.010075 | 0.191851-0.255165 | no aplica | 0.031000 | Aggregate, Bitmap Heap Scan | selectividad 0.0120 |
| agg.q3_noindex.1000.mag4 | q3_noindex | 1000 | mag4 | 15 (15) | 0.220467 | 0.203915-0.223508 | 0.019593 | 0.202360-0.237966 | no aplica | 0.096000 | Aggregate, Seq Scan | selectividad 1.0000 |
| agg.q3_noindex.1000.p99 | q3_noindex | 1000 | p99 | 15 (15) | 0.205138 | 0.196894-0.215064 | 0.018169 | 0.192305-0.239664 | no aplica | 0.058000 | Aggregate, Seq Scan | selectividad 0.0120 |
| agg.q4_noindex.1000.all | q4_noindex | 1000 | all | 15 (15) | 0.694267 | 0.679691-0.735004 | 0.055313 | 0.670260-0.769665 | no aplica | 0.315000 | Aggregate, Sort | selectividad 1.0000 |
| agg.q4_noindex.1000.day | q4_noindex | 1000 | day | 15 (15) | 0.224390 | 0.210294-0.272226 | 0.061933 | 0.206747-0.293326 | no aplica | 0.064000 | Aggregate, Sort | selectividad 0.0430 |
| agg.q4_time_index.1000.all | q4_time_index | 1000 | all | 15 (15) | 0.669548 | 0.664015-0.683836 | 0.019821 | 0.654631-0.714373 | no aplica | 0.276000 | Aggregate, Sort | selectividad 1.0000 |
| agg.q4_time_index.1000.day | q4_time_index | 1000 | day | 15 (15) | 0.181868 | 0.177708-0.230852 | 0.053144 | 0.174734-0.271043 | no aplica | 0.033000 | Aggregate, Sort | selectividad 0.0430 |
| agg.q2_country_index.10000.month | q2_country_index | 10000 | month | 15 (15) | 0.194722 | 0.174574-0.206517 | 0.031943 | 0.168348-0.289723 | no aplica | 0.035000 | Aggregate, Bitmap Heap Scan | selectividad 0.0067 |
| agg.q2_country_index.10000.range | q2_country_index | 10000 | range | 15 (15) | 0.237399 | 0.217394-0.258234 | 0.040840 | 0.190430-0.382764 | no aplica | 0.072000 | Aggregate, Bitmap Heap Scan | selectividad 0.0196 |
| agg.q2_noindex.10000.month | q2_noindex | 10000 | month | 15 (15) | 0.657134 | 0.638938-0.680699 | 0.041761 | 0.627680-0.700331 | no aplica | 0.474000 | Aggregate, Seq Scan | selectividad 0.0067 |
| agg.q2_noindex.10000.range | q2_noindex | 10000 | range | 15 (15) | 0.687240 | 0.673261-0.695422 | 0.022161 | 0.668202-0.746181 | no aplica | 0.585000 | Aggregate, Seq Scan | selectividad 0.0196 |
| agg.q3_mag_index.10000.mag4 | q3_mag_index | 10000 | mag4 | 15 (15) | 0.718848 | 0.696366-0.742308 | 0.045942 | 0.690120-0.809240 | no aplica | 0.907000 | Aggregate, Seq Scan | selectividad 1.0000 |
| agg.q3_mag_index.10000.p99 | q3_mag_index | 10000 | p99 | 15 (15) | 0.184493 | 0.178635-0.197884 | 0.019249 | 0.171629-0.245467 | no aplica | 0.039000 | Aggregate, Bitmap Heap Scan | selectividad 0.0079 |
| agg.q3_noindex.10000.mag4 | q3_noindex | 10000 | mag4 | 15 (15) | 0.715621 | 0.697414-0.736988 | 0.039573 | 0.682780-0.765363 | no aplica | 0.885000 | Aggregate, Seq Scan | selectividad 1.0000 |
| agg.q3_noindex.10000.p99 | q3_noindex | 10000 | p99 | 15 (15) | 0.635278 | 0.609282-0.655633 | 0.046351 | 0.603532-1.032 | no aplica | 0.483000 | Aggregate, Seq Scan | selectividad 0.0079 |
| agg.q4_noindex.10000.all | q4_noindex | 10000 | all | 15 (15) | 3.811 | 3.782-3.854 | 0.072032 | 3.748-3.946 | no aplica | 2.561 | Aggregate, Sort | selectividad 1.0000 |
| agg.q4_noindex.10000.day | q4_noindex | 10000 | day | 15 (15) | 0.505452 | 0.489646-0.521800 | 0.032154 | 0.482150-0.639107 | no aplica | 0.345000 | Aggregate, Sort | selectividad 0.0359 |
| agg.q4_time_index.10000.all | q4_time_index | 10000 | all | 15 (15) | 3.862 | 3.790-3.961 | 0.171843 | 3.733-25.403 | no aplica | 2.554 | Aggregate, Sort | selectividad 1.0000 |
| agg.q4_time_index.10000.day | q4_time_index | 10000 | day | 15 (15) | 0.229941 | 0.224891-0.251801 | 0.026910 | 0.223384-0.274222 | no aplica | 0.093000 | Aggregate, Sort | selectividad 0.0359 |
| agg.q2_country_index.100000.month | q2_country_index | 100000 | month | 15 (15) | 0.182825 | 0.182231-0.184203 | 0.001972 | 0.179862-0.195175 | no aplica | 0.057000 | Aggregate, Index Only Scan | selectividad 0.0058 |
| agg.q2_country_index.100000.range | q2_country_index | 100000 | range | 15 (15) | 0.247712 | 0.246178-0.251815 | 0.005637 | 0.244779-0.325661 | no aplica | 0.167000 | Aggregate, Index Only Scan | selectividad 0.0196 |
| agg.q2_noindex.100000.month | q2_noindex | 100000 | month | 15 (15) | 5.359 | 5.251-5.418 | 0.166339 | 5.093-6.022 | no aplica | 5.582 | Aggregate, Seq Scan | selectividad 0.0058 |
| agg.q2_noindex.100000.range | q2_noindex | 100000 | range | 15 (15) | 5.810 | 5.698-5.911 | 0.212940 | 5.615-7.232 | no aplica | 5.227 | Aggregate, Seq Scan | selectividad 0.0196 |
| agg.q3_mag_index.100000.mag4 | q3_mag_index | 100000 | mag4 | 15 (15) | 4.003 | 3.992-4.052 | 0.060363 | 3.953-5.878 | no aplica | 6.770 | Aggregate, Index Only Scan | selectividad 0.9458 |
| agg.q3_mag_index.100000.p99 | q3_mag_index | 100000 | p99 | 15 (15) | 0.202031 | 0.198882-0.209698 | 0.010815 | 0.197075-0.229250 | no aplica | 0.086000 | Aggregate, Index Only Scan | selectividad 0.0102 |
| agg.q3_noindex.100000.mag4 | q3_noindex | 100000 | mag4 | 15 (15) | 5.956 | 5.860-6.065 | 0.205645 | 5.807-6.640 | no aplica | 8.762 | Aggregate, Seq Scan | selectividad 0.9458 |
| agg.q3_noindex.100000.p99 | q3_noindex | 100000 | p99 | 15 (15) | 5.503 | 5.265-5.943 | 0.678538 | 4.959-6.606 | no aplica | 5.021 | Aggregate, Seq Scan | selectividad 0.0102 |
| agg.q4_noindex.100000.all | q4_noindex | 100000 | all | 15 (15) | 17.247 | 16.988-17.501 | 0.513401 | 16.606-69.652 | no aplica | 24.792 | Aggregate, Sort | selectividad 1.0000 |
| agg.q4_noindex.100000.day | q4_noindex | 100000 | day | 15 (15) | 3.526 | 3.483-3.604 | 0.120722 | 3.420-4.904 | no aplica | 3.375 | Sort, Aggregate | selectividad 0.0184 |
| agg.q4_time_index.100000.all | q4_time_index | 100000 | all | 15 (15) | 17.316 | 17.075-17.831 | 0.755400 | 16.649-18.443 | no aplica | 22.357 | Aggregate, Sort | selectividad 1.0000 |
| agg.q4_time_index.100000.day | q4_time_index | 100000 | day | 15 (15) | 0.375212 | 0.369404-0.391134 | 0.021730 | 0.367426-0.484703 | no aplica | 0.329000 | Aggregate, Sort | selectividad 0.0184 |
