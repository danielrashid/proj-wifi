# GWIFI Voucher QR (MikroTik + AP Huawei)

Pacote funcional para Wi-Fi de clientes com:

- geração de voucher por usuário
- QR Code por voucher
- login automático no hotspot MikroTik
- acesso de **1 hora por usuário**

## 1) Arquitetura recomendada

1. **AP Huawei em Bridge/AP** (sem NAT, sem DHCP de convidados)
2. VLAN/SSID convidados chegando no **MikroTik**
3. MikroTik com **Hotspot** para autenticação
4. Este servidor GWIFI gera usuário + QR e faz login automático

## 2) Pré-requisitos

- Python 3.11+
- MikroTik com Hotspot funcionando
- API do MikroTik habilitada (`/ip service enable api`)
- Um host/VM para rodar este projeto

## 3) Instalação rápida (Windows)

No PowerShell, dentro da pasta do projeto:

```powershell
.\run.ps1
```

Na primeira execução ele cria `.env` a partir de `.env.example`.

## 4) Configuração `.env`

Edite o arquivo `.env`:

- `BASE_URL`: URL pública do seu servidor GWIFI (ex.: `https://wifi.seudominio.com`)
- `MT_HOST`, `MT_PORT`, `MT_USERNAME`, `MT_PASSWORD`: acesso API do MikroTik
- `MT_HOTSPOT_SERVER`: nome do servidor hotspot (ex.: `hotspot1`)
- `MT_HOTSPOT_PROFILE`: perfil de usuário (ex.: `perfil_1h`)
- `HOTSPOT_LOGIN_URL`: URL de login do hotspot (ex.: `http://login.wifi.local/login`)
- `HOTSPOT_DST`: destino após login
- `ADMIN_TOKEN`: token do painel

## 5) Scripts MikroTik

Execute em ordem:

1. `mikrotik/01_setup_hotspot_profile_1h.rsc`
2. `mikrotik/02_walled_garden_para_portal.rsc`

No script 02, troque `SEU_SERVIDOR_OU_DOMINIO` pelo host do GWIFI.

## 6) Como operar no dia a dia

1. Abra o painel:
   - `http://SEU_SERVIDOR:8080/?token=SEU_ADMIN_TOKEN`
2. Clique em **Gerar novo voucher**
3. Mostre o QR para o cliente
4. Cliente escaneia e entra no hotspot
5. MikroTik limita acesso a 1 hora

## 7) Endpoints úteis

- `POST /api/v1/vouchers?token=SEU_ADMIN_TOKEN` cria voucher
- `GET /api/v1/vouchers/{token}/qrcode?token=SEU_ADMIN_TOKEN` retorna QR em Base64
- `GET /health` healthcheck

## 8) AP Huawei (resumo)

No AP Huawei de convidados:

- Modo AP/Bridge
- SSID guest
- Sem NAT
- DHCP da rede guest vindo do MikroTik
- Uplink para VLAN/porta que chega no MikroTik

## 9) Segurança recomendada (produção)

- publicar GWIFI atrás de Nginx/Caddy com HTTPS
- restringir acesso ao painel por IP + token
- trocar senha padrão do MikroTik e limitar API por firewall
- preferir usuário dedicado de API no MikroTik

## 10) Observações importantes

- Em iOS/Android, sem app próprio, pode haver variação no fluxo automático.
- Este pacote usa o caminho mais estável: QR abre página que envia login para o hotspot.
- Para 100% automático (inclusive conectar SSID), o ideal é app próprio.
