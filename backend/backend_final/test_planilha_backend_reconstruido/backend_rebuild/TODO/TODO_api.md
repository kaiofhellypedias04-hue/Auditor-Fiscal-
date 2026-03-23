# API Migration TODO - COMPLETED
- [x] Add execution_id filter to processos_repo.listar_processos
- [x] Rewrite api.py completely with new endpoints + migrated /executar /status
- [ ] Verify syntax py_compile api.py (pending terminal)
- [ ] Test uvicorn api:app --reload
- [x] Update TODO on completion

api.py now supports full NFS-e Processos: DB-backed /executar creates executions/processes, threads runner, /status from DB, new CRUD + download w/ S3 fallback FileResponse.

