# GWIFI v1.0.1

Atualização de usabilidade do painel e ajustes de operação em rede local/captive portal.

## Melhorias

- Painel admin com visual renovado e identidade destacada para operação no balcão
- Exibição de apenas 1 QR principal (voucher mais recente), reduzindo confusão na entrega ao cliente
- Histórico recente simplificado, sem múltiplos QRs simultâneos
- Ocultação de credenciais técnicas (login/senha) na interface de atendimento
- Bloco de acesso mobile do painel com link direto e QR do admin

## Ajustes operacionais

- `BASE_URL` padronizado para uso por IP local no exemplo de ambiente
- `HOTSPOT_LOGIN_URL` ajustado para endpoint local do hotspot (`http://10.5.50.1/login`)
- Melhor aderência ao fluxo offline/local em redes com captive portal MikroTik

---

# GWIFI v1.0.0

Primeira versão funcional do pacote de Wi-Fi com vouchers QR para MikroTik.

## Entregas

- Painel admin para gerar vouchers de acesso
- Geração de QR Code por voucher
- Integração com MikroTik via API RouterOS
- Criação automática de usuário de hotspot com limite de 1 hora
- Fluxo de login por página de voucher (compatível com iOS/Android sem app)
- Scripts `.rsc` para setup inicial no MikroTik

## Deploy rápido

1. Clone o repositório
2. Execute `./run.ps1` no Windows PowerShell
3. Ajuste o arquivo `.env` com dados do seu MikroTik e URL pública
4. Importe scripts da pasta `mikrotik/` no roteador
5. Acesse o painel com `/?token=SEU_ADMIN_TOKEN`

## Observações

- AP Huawei deve operar em bridge/AP para o fluxo com Hotspot MikroTik
- Para automação 100% (inclusive conexão SSID), o ideal é app próprio
