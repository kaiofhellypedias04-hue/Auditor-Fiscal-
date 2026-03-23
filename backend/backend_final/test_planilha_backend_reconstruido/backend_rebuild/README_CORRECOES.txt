Pacote reconstruído com base no backend original + correções aplicadas:
- fluxo Playwright restaurado com leitura de senha via keyring e envio por PFX_PASS/LOGIN_PASS
- erro detalhado do Playwright propagado até o runner
- CORS local flexível (localhost/127.0.0.1 em qualquer porta)
- /execucoes ajustado para não usar MIN(jsonb)
- runner repropaga erro quando estiver em modo processo/API

Antes de rodar:
1) pip install -r requirements.txt (se houver) e dependências Python do projeto
2) npm install
3) npx playwright install
4) configurar certs.json / credentials.json
5) configurar senhas no keyring/cofre
