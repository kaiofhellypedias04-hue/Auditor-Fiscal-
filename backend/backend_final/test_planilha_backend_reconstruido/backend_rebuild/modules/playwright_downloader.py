from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from .cert_manager import get_password, get_credential_password


def _run_node_download(
    script_path: str,
    cert_alias: str,
    data_inicial: str,
    data_final: str,
    download_dir: str,
    certs_json_path: str,
    credentials_json_path: str,
    login_type: str = "certificado",
    headless: bool = False,
    tipo_nota: str = "tomados",
) -> Dict[str, Any]:
    env = os.environ.copy()

    node_opts = env.get("NODE_OPTIONS", "")
    if "--openssl-legacy-provider" not in node_opts:
        env["NODE_OPTIONS"] = (node_opts + " " if node_opts else "") + "--openssl-legacy-provider"

    env["CERTS_JSON"] = certs_json_path
    env["CREDENTIALS_JSON"] = credentials_json_path
    env["LOGIN_TYPE"] = login_type

    try:
        if login_type == "certificado":
            pfx_pass = get_password(cert_alias)
            if not pfx_pass:
                return {
                    "ok": False,
                    "error": f"Senha não configurada no cofre para o certificado: {cert_alias}. Use a opção 'Gerenciar Certificados (PFX)' na interface.",
                    "stdout": "",
                    "stderr": "",
                    "returncode": None,
                }
            env["PFX_PASS"] = pfx_pass
        else:
            portal_pass = get_credential_password(cert_alias)
            if not portal_pass:
                return {
                    "ok": False,
                    "error": f"Senha não configurada no cofre para a credencial: {cert_alias}. Use a opção 'Gerenciar Credenciais' na interface.",
                    "stdout": "",
                    "stderr": "",
                    "returncode": None,
                }
            env["LOGIN_PASS"] = portal_pass

        proc = subprocess.run(
            [
                "node",
                script_path,
                "--alias", cert_alias,
                "--dataInicial", data_inicial,
                "--dataFinal", data_final,
                "--downloadDir", download_dir,
                "--certsJson", certs_json_path,
                "--credentialsJson", credentials_json_path,
                "--loginType", login_type,
                "--headless", "true" if headless else "false",
                "--tipoNota", tipo_nota,
            ],
            cwd=os.path.dirname(script_path),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "Node.js não encontrado no PATH",
            "stdout": "",
            "stderr": "",
            "returncode": None,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"Erro executando subprocess do Playwright: {e}",
            "stdout": "",
            "stderr": "",
            "returncode": None,
        }

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    payload: Dict[str, Any] = {
        "ok": False,
        "error": None,
        "stdout": stdout,
        "stderr": stderr,
        "returncode": proc.returncode,
    }

    parsed: Optional[Dict[str, Any]] = None
    for text in (stdout, stderr):
        if not text:
            continue
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            continue
        last = lines[-1]
        try:
            maybe = json.loads(last)
            if isinstance(maybe, dict):
                parsed = maybe
                break
        except Exception:
            pass

    if parsed is not None:
        payload.update(parsed)
        payload.setdefault("stdout", stdout)
        payload.setdefault("stderr", stderr)
        payload.setdefault("returncode", proc.returncode)
        if "ok" not in payload:
            payload["ok"] = proc.returncode == 0
        if not payload.get("ok") and not payload.get("error"):
            payload["error"] = stderr or stdout or f"Node retornou código {proc.returncode} sem mensagem detalhada"
        return payload

    if proc.returncode == 0:
        payload["ok"] = True
        return payload

    payload["error"] = stderr or stdout or f"Playwright retornou código {proc.returncode} sem saída parseável"
    return payload


def executar_fluxo_nfse_playwright(
    cert_alias: str,
    data_inicial: str,
    data_final: str,
    diretorio_base: str,
    certs_json_path: str,
    credentials_json_path: str,
    login_type: str = "certificado",
    headless: bool = False,
    download_dir: str | None = None,
    tipo_nota: str = "tomados",
) -> Tuple[bool, int, bool, Optional[str]]:
    projeto_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    script_path = os.path.join(projeto_root, "playwright_nfse_download.js")
    if not os.path.exists(script_path):
        return False, 0, False, f"Script Playwright não encontrado: {script_path}"

    os.makedirs(diretorio_base, exist_ok=True)
    if download_dir is None:
        download_dir = os.path.join(diretorio_base, "tmp_downloads", datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(download_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print("PLAYWRIGHT: LOGIN + DOWNLOAD")
    print(f"Alias: {cert_alias}")
    print(f"Login type: {login_type}")
    print(f"Período: {data_inicial} até {data_final}")
    print(f"Download dir: {download_dir}")
    print(f"Tipo nota: {tipo_nota}")
    print(f"{'='*60}")

    max_tentativas = 5
    result: Dict[str, Any] = {}
    login_desc = f"{login_type}:{cert_alias}"

    for tentativa in range(1, max_tentativas + 1):
        try:
            if os.path.isdir(download_dir):
                for nome in os.listdir(download_dir):
                    caminho = os.path.join(download_dir, nome)
                    if os.path.isfile(caminho):
                        try:
                            os.remove(caminho)
                        except Exception:
                            pass
        except Exception:
            pass

        print(f"▶️ Tentativa {tentativa}/{max_tentativas} - {login_desc}")
        result = _run_node_download(
            script_path=script_path,
            cert_alias=cert_alias,
            data_inicial=data_inicial,
            data_final=data_final,
            download_dir=download_dir,
            certs_json_path=certs_json_path,
            credentials_json_path=credentials_json_path,
            login_type=login_type,
            headless=headless,
            tipo_nota=tipo_nota,
        )

        if result.get("ok"):
            total_xml = int(result.get("totalXml") or 0)
            total_pdf = int(result.get("totalPdf") or 0)
            print(f"✅ Download concluído ({login_desc}) - XML: {total_xml} | PDF: {total_pdf}")
            return True, total_xml, bool(result.get("needToSplit")), None

        error_msg = (
            result.get("error")
            or (result.get("stderr") or "").strip()
            or (((result.get("stdout") or "").strip()[:500] + "...") if (result.get("stdout") or "").strip() else "")
            or "erro desconhecido no Playwright"
        )
        print(f"❌ Playwright falhou para {login_desc}: {error_msg}")

        msg_lower = str(error_msg).lower()
        eh_falha_login = (
            "falha no login" in msg_lower
            or "/emissornacional/login" in msg_lower
            or "login/index" in msg_lower
            or ("certificado" in msg_lower and "login" in msg_lower)
        )
        if eh_falha_login and tentativa < max_tentativas:
            wait_time = min(10 + tentativa * 5, 30)
            print(f"⏳ Aguardando {wait_time} segundos antes de tentar novamente...")
            time.sleep(wait_time)
            continue
        return False, 0, False, str(error_msg)

    error_msg = (
        result.get("error")
        or (result.get("stderr") or "").strip()
        or (((result.get("stdout") or "").strip()[:500] + "...") if (result.get("stdout") or "").strip() else "")
        or "Falha após todas as tentativas do Playwright"
    )
    return False, 0, False, str(error_msg)
