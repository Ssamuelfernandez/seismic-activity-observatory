# Equipo de medición

Las filas «VM de Docker Desktop» están leídas de la máquina que ejecuta las mediciones (la VM de Docker Desktop sobre WSL2). Las filas «Anfitrión» las aporta el alumno (SUPUESTO: no se han medido aquí). Los recursos asignados a Docker se leyeron con `docker info` el 2026-11-13.

## VM de Docker Desktop (donde corren las mediciones)

| Campo | Valor |
|---|---|
| Modelo de CPU | AMD Ryzen 9 9900X 12-Core Processor |
| Núcleos físicos | 12 |
| Núcleos lógicos | 24 |
| RAM total | 15.17 GiB |
| Sistema operativo | Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.36 |
| Python | 3.12.16 |
| PostgreSQL | PostgreSQL 16.15 (Debian 16.15-1.pgdg12+2) on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14+deb12u1) 12.2.0, 64-bit |
| shapely | 2.2.0 |
| Límite de CPU del contenedor | Sin límite (`NanoCpus=0` en los 5 contenedores de Compose, leído con `docker inspect` el 2026-11-14; usan las 24 CPU de la VM) |
| Límite de memoria del contenedor | Sin límite (`Memory=0` en los 5 contenedores; usan hasta los 15,17 GiB de la VM) |

## Recursos asignados a Docker (leídos del sistema)

Origen: `docker info` (Docker Desktop, kernel 6.6.87.2-microsoft-standard-WSL2).

| Campo | Valor |
|---|---|
| CPU asignadas (`NCPU`) | 24 (todos los núcleos lógicos del anfitrión) |
| Memoria asignada (`MemTotal`) | 16 290 832 384 B = 15.17 GiB |
| Configuración propia | No existe `.wslconfig`: se usan los valores por defecto de WSL2 |

## Equipo anfitrión (aportado por el alumno)

| Campo | Valor |
|---|---|
| CPU | AMD Ryzen 9 9900X, 12 núcleos, 4,40 GHz |
| RAM | 32 GB DDR5 a 4800 MT/s (31,1 GB utilizables) |
| GPU | NVIDIA GeForce RTX 3060 Ti 8 GB + gráficos Radeon integrados |
| Almacenamiento | 1,82 TB |
| Sistema operativo | Windows, 64 bits |
| Potencia del equipo anfitrión | 100 W; SUPUESTO (no medida) |
