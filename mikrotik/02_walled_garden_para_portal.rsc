# Permitir acesso ao seu portal antes do login no hotspot
# Troque o domínio/host abaixo para o host do seu servidor GWIFI

:local portalHost "SEU_SERVIDOR_OU_DOMINIO"

/ip hotspot walled-garden ip add dst-host=$portalHost action=accept

# Opcional para APIs públicas de CRL/CDN caso precise
# /ip hotspot walled-garden ip add dst-host="*.cloudflare.com" action=accept
# /ip hotspot walled-garden ip add dst-host="*.google.com" action=accept

/ip hotspot walled-garden ip print
