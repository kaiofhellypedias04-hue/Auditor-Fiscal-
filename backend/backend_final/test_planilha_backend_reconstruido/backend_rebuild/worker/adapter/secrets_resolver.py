"""Secrets resolution for certs/credentials by ID."""
import keyring
from typing import Optional, Tuple
from pydantic import ValidationError
from .schemas import APIInputPayload, ErrorCode
from ..models import ErrorCode as LegacyErrorCode

# Mock DB (future: integrate modules.db)
_MOCK_CERTS_DB = {
    'cert-001': {'path': '/mock/path/to/cert.pfx', 'service': 'nfse_auditoria'},
    'cert-002': {'path': '/mock/path/to/other.pfx', 'service': 'nfse_auditoria'},
}
_MOCK_CREDS_DB = {
    'cred-001': {'username': '12.345.678/0001-99', 'service': 'nfse_auditoria_credentials'},
}

class SecretsResolver:
    @staticmethod
    def resolve_certificate(cert_id: str) -> Tuple[Optional[str], Optional[str]]:
        if cert_id not in _MOCK_CERTS_DB:
            raise ValueError(LegacyErrorCode.CERTIFICATE_NOT_FOUND.value)
        
        cert_info = _MOCK_CERTS_DB[cert_id]
        path = cert_info['path']
        
        # Validate PFX exists
        import os
        if not os.path.exists(path):
            raise ValueError(LegacyErrorCode.CERTIFICATE_INVALID.value)
        
        # Get password from keyring
        password = keyring.get_password(cert_info['service'], cert_id)
        if not password:
            raise ValueError(LegacyErrorCode.CERTIFICATE_INVALID.value + ': missing password')
        
        return path, password

    @staticmethod
    def resolve_credential(cred_id: str) -> Tuple[Optional[str], Optional[str]]:
        if cred_id not in _MOCK_CREDS_DB:
            raise ValueError(LegacyErrorCode.CREDENTIAL_NOT_FOUND.value)
        
        cred_info = _MOCK_CREDS_DB[cred_id]
        username = cred_info['username']
        password = keyring.get_password(cred_info['service'], cred_id)
        if not password:
            raise ValueError(LegacyErrorCode.LOGIN_FAILED.value + ': missing credential password')
        
        return username, password

    @staticmethod
    def resolve(payload: APIInputPayload) -> dict:
        """Resolve secrets into dict for context."""
        secrets = {}
        if payload.loginType == 'certificado' and payload.certificateId:
            secrets['cert_path'], secrets['cert_password'] = SecretsResolver.resolve_certificate(payload.certificateId)
        elif payload.loginType == 'cpf_cnpj' and payload.credentialId:
            secrets['cred_username'], secrets['cred_password'] = SecretsResolver.resolve_credential(payload.credentialId)
        else:
            # Legacy: expect paths/pwds in payload (but sanitized; error if needed)
            pass  # Future handling
        
        return secrets

