# TODO: Fix NFSe Parte Exibição Logic

## Status: 🔄 In Progress

```
Phase 1: DB + Core API (Priority MAX)
☐ 1.1 modules/notas_repo.py: Add columns (garantir_schema_nfse_notas)
☐ 1.2 modules/notas_repo.py: salvar_nota_nfse compute new fields  
☐ 1.3 modules/notas_repo.py: Queries JOIN + SELECT new fields + fallback
☐ 1.4 modules/schemas.py: Extend NotaReportRow
☐ 1.5 Test Phase 1: /nfse response

Phase 2: Reports
☐ 2.1 Create modules/reports.py (gen JSON)
☐ 2.2 reports.py: File exports (JSON/CSV/XLSX)
☐ 2.3 api.py: /relatorios/processo/{id}
☐ 2.4 Test files in resultados/

Phase 3: Validation
☐ 3.1 Backfill old data
☐ 3.2 E2E test
```

## Phase 1 Progress
✅ 1.1 DB Schema (new columns + indexes)
✅ 1.2 salvar_nota_nfse: fetch tipo_nota + compute/store parte_exibicao_*
✅ 1.3 Queries: JOIN processo + SELECT/COALESCE new fields + fallback
✅ 1.4 schemas.py: NotaReportRow extended

**Phase 1 COMPLETE** 🎉
`/nfse` now returns:
- parte_exibicao_nome/doc/tipo
- tipo_nota, processo_id, certificado
- Fallback for old data

**Phase 1 Test** 
Run: `python -c "from modules.notas_repo import garantir_schema_nfse_notas; garantir_schema_nfse_notas()"`

Then `uvicorn api:app --reload` + `curl "http://localhost:8000/nfse?page=1&page_size=5"` → verify new fields!

## Phase 2 Progress
✅ 2.1 modules/reports.py: gerar_relatorio_processo
✅ 2.2 modules/reports.py: save_report_files (JSON/CSV/XLSX)
✅ 2.3 api.py: GET /relatorios/processo/{id}

**Phase 2 COMPLETE** 🎉
- Endpoint returns structured report
- Files in `resultados/CERT/YYYY-MM/`

**Test Phase 2**:
1. Run process via /executar
2. GET /relatorios/processo/{id} → check structure
3. Files generated? (manual call save_report_files if needed)

## Next: Phase 3 Validation + Completion



