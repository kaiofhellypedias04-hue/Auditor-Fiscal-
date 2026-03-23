"""
Gerenciamento de certificados (.pfx) e credenciais CPF/CNPJ.

- Caminhos dos certificados ficam em certs.json (no root do projeto)
- Credenciais CPF/CNPJ ficam em credentials.json (no root do projeto)
- Senhas ficam armazenadas no cofre do Windows (DPAPI) via keyring

Service usado no keyring: "nfse_auditoria"
Username: alias do certificado ou credencial
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Optional

SERVICE_NAME = "nfse_auditoria"
CREDENTIALS_SERVICE = "nfse_auditoria_credentials"


def _ensure_keyring():
    try:
        import keyring  # noqa
        return True, None
    except Exception as e:
        return False, str(e)


# ─── Validação de CPF/CNPJ ────────────────────────────────────────────────────

def _apenas_digitos(s: str) -> str:
    return re.sub(r"\D", "", s)


def _validar_cpf(cpf: str) -> bool:
    c = _apenas_digitos(cpf)
    if len(c) != 11 or len(set(c)) == 1:
        return False
    # Dígito 1
    soma = sum(int(c[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10 % 11) % 10
    if d1 != int(c[9]):
        return False
    # Dígito 2
    soma = sum(int(c[i]) * (11 - i) for i in range(10))
    d2 = (soma * 10 % 11) % 10
    return d2 == int(c[10])


def _validar_cnpj(cnpj: str) -> bool:
    c = _apenas_digitos(cnpj)
    if len(c) != 14 or len(set(c)) == 1:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(c[i]) * pesos1[i] for i in range(12))
    d1 = 0 if soma % 11 < 2 else 11 - (soma % 11)
    if d1 != int(c[12]):
        return False
    soma = sum(int(c[i]) * pesos2[i] for i in range(13))
    d2 = 0 if soma % 11 < 2 else 11 - (soma % 11)
    return d2 == int(c[13])


def validar_cpf_cnpj(valor: str) -> bool:
    """Retorna True se o valor é um CPF ou CNPJ válido."""
    digitos = _apenas_digitos(valor)
    if len(digitos) == 11:
        return _validar_cpf(digitos)
    if len(digitos) == 14:
        return _validar_cnpj(digitos)
    return False


# ─── Utilitários de arquivo ───────────────────────────────────────────────────

def _projeto_root() -> Path:
    """Retorna o diretório raiz do projeto (onde ficam certs.json e credentials.json)."""
    return Path(__file__).resolve().parent.parent


def _certs_path() -> str:
    return str(_projeto_root() / "certs.json")


def _credentials_path() -> str:
    return str(_projeto_root() / "credentials.json")


def _certs_dir() -> Path:
    p = _projeto_root() / "certs"
    p.mkdir(parents=True, exist_ok=True)
    return p


# ─── Certificados ─────────────────────────────────────────────────────────────

def load_certs(certs_json_path: str) -> List[Dict]:
    if not os.path.exists(certs_json_path):
        return []
    with open(certs_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        return []
    out = []
    for item in data:
        if not isinstance(item, dict):
            continue
        alias = (item.get("alias") or "").strip()
        pfxPath = (item.get("pfxPath") or "").strip()
        if not alias or not pfxPath:
            continue
        out.append({"alias": alias, "pfxPath": pfxPath})
    return out


def save_certs(certs_json_path: str, certs: List[Dict]) -> None:
    dir_path = os.path.dirname(certs_json_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(certs_json_path, "w", encoding="utf-8") as f:
        json.dump(certs, f, ensure_ascii=False, indent=2)


def get_password(alias: str) -> Optional[str]:
    ok, err = _ensure_keyring()
    if not ok:
        raise RuntimeError(f"keyring não disponível ({err})")
    import keyring
    return keyring.get_password(SERVICE_NAME, alias)


def set_password(alias: str, password: str) -> None:
    ok, err = _ensure_keyring()
    if not ok:
        raise RuntimeError(f"keyring não disponível ({err})")
    import keyring
    keyring.set_password(SERVICE_NAME, alias, password)


def delete_password(alias: str) -> None:
    ok, err = _ensure_keyring()
    if not ok:
        raise RuntimeError(f"keyring não disponível ({err})")
    import keyring
    try:
        keyring.delete_password(SERVICE_NAME, alias)
    except keyring.errors.PasswordDeleteError:
        pass


def upsert_cert(certs_json_path: str, alias: str, pfxPath: str) -> List[Dict]:
    certs = load_certs(certs_json_path)
    alias_n = alias.strip()
    pfx_n = pfxPath.strip()
    updated = False
    for c in certs:
        if c.get("alias") == alias_n:
            c["pfxPath"] = pfx_n
            updated = True
            break
    if not updated:
        certs.append({"alias": alias_n, "pfxPath": pfx_n})
    save_certs(certs_json_path, certs)
    return certs


def remove_cert(certs_json_path: str, alias: str) -> List[Dict]:
    certs = [c for c in load_certs(certs_json_path) if c.get("alias") != alias]
    save_certs(certs_json_path, certs)
    return certs


# ─── Credenciais ──────────────────────────────────────────────────────────────

def load_credentials(credentials_json_path: str) -> List[Dict]:
    if not os.path.exists(credentials_json_path):
        return []
    try:
        with open(credentials_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        out = []
        for item in data:
            if not isinstance(item, dict):
                continue
            alias = (item.get("alias") or "").strip()
            cpf_cnpj = (item.get("cpf_cnpj") or "").strip()
            if not alias or not cpf_cnpj:
                continue
            out.append({"alias": alias, "cpf_cnpj": cpf_cnpj})
        return out
    except Exception:
        return []


def save_credentials(credentials_json_path: str, creds: List[Dict]) -> None:
    dir_path = os.path.dirname(credentials_json_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(credentials_json_path, "w", encoding="utf-8") as f:
        json.dump(creds, f, ensure_ascii=False, indent=2)


def get_credential_password(alias: str) -> Optional[str]:
    ok, err = _ensure_keyring()
    if not ok:
        raise RuntimeError(f"keyring não disponível ({err})")
    import keyring
    return keyring.get_password(CREDENTIALS_SERVICE, alias)


def set_credential_password(alias: str, password: str) -> None:
    ok, err = _ensure_keyring()
    if not ok:
        raise RuntimeError(f"keyring não disponível ({err})")
    import keyring
    keyring.set_password(CREDENTIALS_SERVICE, alias, password)


def delete_credential_password(alias: str) -> None:
    ok, err = _ensure_keyring()
    if not ok:
        raise RuntimeError(f"keyring não disponível ({err})")
    import keyring
    try:
        keyring.delete_password(CREDENTIALS_SERVICE, alias)
    except keyring.errors.PasswordDeleteError:
        pass


def upsert_credential(credentials_json_path: str, alias: str, cpf_cnpj: str) -> List[Dict]:
    creds = load_credentials(credentials_json_path)
    alias_n = alias.strip()
    cpf_cnpj_n = cpf_cnpj.strip()
    updated = False
    for c in creds:
        if c.get("alias") == alias_n:
            c["cpf_cnpj"] = cpf_cnpj_n
            updated = True
            break
    if not updated:
        creds.append({"alias": alias_n, "cpf_cnpj": cpf_cnpj_n})
    save_credentials(credentials_json_path, creds)
    return creds


def remove_credential(credentials_json_path: str, alias: str) -> List[Dict]:
    creds = [c for c in load_credentials(credentials_json_path) if c.get("alias") != alias]
    save_credentials(credentials_json_path, creds)
    return creds


# ─── API pública ──────────────────────────────────────────────────────────────

def adicionar_certificado(alias: str, client_name: str, pfx_bytes: bytes, password: str) -> dict:
    """
    Salva o arquivo .pfx no diretório certs/ do projeto (caminho absoluto)
    e registra em certs.json com caminho absoluto para evitar problemas
    ao iniciar a API de diretórios diferentes.
    """
    certs_json = _certs_path()
    cert_file = _certs_dir() / f"{alias}.pfx"

    cert_file.write_bytes(pfx_bytes)
    upsert_cert(certs_json, alias, str(cert_file))
    set_password(alias, password)

    return {
        "alias": alias,
        "client_name": client_name,
        "pfxPath": str(cert_file),
    }


def editar_certificado(alias: str, novo_alias: Optional[str] = None, client_name: Optional[str] = None) -> dict:
    """
    Renomeia o alias no certs.json (e move o arquivo .pfx se necessário).
    client_name é apenas informativo (não é salvo no certs.json, vem do alias).
    """
    certs_json = _certs_path()
    certs = load_certs(certs_json)

    cert = next((c for c in certs if c.get("alias") == alias), None)
    if not cert:
        raise ValueError(f"Certificado '{alias}' não encontrado")

    if novo_alias and novo_alias != alias:
        # Verificar se novo alias já existe
        if any(c.get("alias") == novo_alias for c in certs):
            raise ValueError(f"Alias '{novo_alias}' já está em uso")

        # Mover arquivo .pfx
        old_path = Path(cert["pfxPath"])
        new_path = _certs_dir() / f"{novo_alias}.pfx"
        if old_path.exists():
            old_path.rename(new_path)

        # Migrar senha no keyring
        try:
            senha = get_password(alias)
            if senha:
                set_password(novo_alias, senha)
                delete_password(alias)
        except Exception:
            pass

        # Atualizar certs.json
        remove_cert(certs_json, alias)
        upsert_cert(certs_json, novo_alias, str(new_path))

        return {"alias": novo_alias, "pfxPath": str(new_path)}

    return {"alias": alias, "pfxPath": cert["pfxPath"]}


def redefinir_senha_certificado(alias: str, nova_senha: str) -> bool:
    """Atualiza a senha do certificado no keyring."""
    certs_json = _certs_path()
    certs = load_certs(certs_json)
    if not any(c.get("alias") == alias for c in certs):
        raise ValueError(f"Certificado '{alias}' não encontrado")
    set_password(alias, nova_senha)
    return True


def excluir_certificado(alias: str, remover_arquivo: bool = True) -> bool:
    """Remove o certificado do certs.json, do keyring e opcionalmente o arquivo .pfx."""
    certs_json = _certs_path()
    certs = load_certs(certs_json)
    cert = next((c for c in certs if c.get("alias") == alias), None)
    if not cert:
        raise ValueError(f"Certificado '{alias}' não encontrado")

    if remover_arquivo:
        pfx = Path(cert.get("pfxPath", ""))
        if pfx.exists():
            pfx.unlink(missing_ok=True)

    remove_cert(certs_json, alias)
    delete_password(alias)
    return True


def adicionar_credencial(alias: str, cpf_cnpj: str, password: str) -> dict:
    """
    Cadastra credencial após validar CPF/CNPJ.
    Lança ValueError se o documento for inválido.
    """
    if not validar_cpf_cnpj(cpf_cnpj):
        raise ValueError(
            f"CPF/CNPJ inválido: '{cpf_cnpj}'. "
            "Informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido."
        )

    credentials_json = _credentials_path()
    upsert_credential(credentials_json, alias, cpf_cnpj)
    set_credential_password(alias, password)

    return {"alias": alias, "cpf_cnpj": cpf_cnpj}


def editar_credencial(alias: str, novo_alias: Optional[str] = None, cpf_cnpj: Optional[str] = None) -> dict:
    """Edita alias e/ou CPF/CNPJ de uma credencial existente."""
    credentials_json = _credentials_path()
    creds = load_credentials(credentials_json)

    cred = next((c for c in creds if c.get("alias") == alias), None)
    if not cred:
        raise ValueError(f"Credencial '{alias}' não encontrada")

    if cpf_cnpj and not validar_cpf_cnpj(cpf_cnpj):
        raise ValueError(f"CPF/CNPJ inválido: '{cpf_cnpj}'")

    novo_cpf = cpf_cnpj or cred["cpf_cnpj"]
    destino_alias = (novo_alias or alias).strip()

    if destino_alias != alias:
        if any(c.get("alias") == destino_alias for c in creds):
            raise ValueError(f"Alias '{destino_alias}' já está em uso")
        try:
            senha = get_credential_password(alias)
            if senha:
                set_credential_password(destino_alias, senha)
                delete_credential_password(alias)
        except Exception:
            pass
        remove_credential(credentials_json, alias)

    upsert_credential(credentials_json, destino_alias, novo_cpf)
    return {"alias": destino_alias, "cpf_cnpj": novo_cpf}


def redefinir_senha_credencial(alias: str, nova_senha: str) -> bool:
    """Atualiza a senha da credencial no keyring."""
    credentials_json = _credentials_path()
    creds = load_credentials(credentials_json)
    if not any(c.get("alias") == alias for c in creds):
        raise ValueError(f"Credencial '{alias}' não encontrada")
    set_credential_password(alias, nova_senha)
    return True


def excluir_credencial(alias: str) -> bool:
    """Remove a credencial do credentials.json e do keyring."""
    credentials_json = _credentials_path()
    creds = load_credentials(credentials_json)
    if not any(c.get("alias") == alias for c in creds):
        raise ValueError(f"Credencial '{alias}' não encontrada")
    remove_credential(credentials_json, alias)
    delete_credential_password(alias)
    return True
