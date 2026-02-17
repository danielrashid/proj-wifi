# Execute no terminal do MikroTik
# Ajuste o nome do servidor hotspot se necessário

:local hsServer "hotspot1"
:local profileName "perfil_1h"

/ip hotspot profile set [find] login-by=http-pap,http-chap,cookie

:if ([:len [/ip hotspot user profile find where name=$profileName]] = 0) do={
  /ip hotspot user profile add name=$profileName session-timeout=1h idle-timeout=5m shared-users=1 status-autorefresh=1m
}

# Opcional: validar
/ip hotspot user profile print where name=$profileName
