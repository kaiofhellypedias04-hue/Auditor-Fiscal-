# WORKER REFACTOR IMPLEMENTATION PLAN
Status: [COMPLETED ✅]

## Detailed Steps (Execute Sequentially)

### 1. Update Models [PENDING]
- Edit `worker/models.py`: Extend ErrorCode with all required codes; Add PydanticBase for schemas.

### 2. Structured Logging [PENDING]
- Create/Update `worker/logging.py`: Implement StructuredLogger with truncation (10k chars).

### 3. Adapter Schemas [PENDING]
- Create `worker/adapter/schemas.py`: Pydantic models (APIInputPayload, ExecutionContext, RunnerPayload).

### 4. Secrets Resolver [PENDING]
- Create `worker/adapter/secrets_resolver.py`: Resolve cert/cred by ID (keyring/DB mock; legacy fallback).

### 5. Temp Manager [PENDING]
- Create `worker/adapter/temp_manager.py`: Handle temp json/dir; cleanup unless debug.

### 6. Mapper [PENDING]
- Create `worker/adapter/mapper.py`: api_payload → context (validate loginType) → runner_cfg.

### 7. Executor [PENDING]
- Create `worker/adapter/executor.py`: Orchestrate mapper/secrets/temp → run_processing → result.

### 8. Adapter Init [PENDING]
- Create `worker/adapter/__init__.py`: Exports.

### 9. Update Runner CLI [PENDING]
- Edit `worker/runner.py`: CLI → executor.execute().

### 10. Sanitize Example [PENDING]
- Edit `worker/payload.example.json`: Add certificateId/credentialId; remove passwords.

### 11. Update Worker TODO [PENDING]
- Edit `projeto_invertexto_adaptado_v2/test_planilha/TODO_WORKER.md`: Mark complete.

### 12. Test & Verify [PENDING]
- Test CLI; check cleanup, errors, validation.

## Progress Tracking
- Update ✅ after each step completion.
- Final: attempt_completion with summary.

