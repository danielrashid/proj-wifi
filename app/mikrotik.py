from dataclasses import dataclass

import routeros_api


class MikroTikError(Exception):
    pass


@dataclass
class MikroTikConfig:
    host: str
    port: int
    username: str
    password: str
    use_ssl: bool
    hotspot_server: str
    hotspot_profile: str


class MikroTikClient:
    def __init__(self, cfg: MikroTikConfig):
        self.cfg = cfg

    def _connect(self):
        try:
            connection = routeros_api.RouterOsApiPool(
                host=self.cfg.host,
                username=self.cfg.username,
                password=self.cfg.password,
                port=self.cfg.port,
                use_ssl=self.cfg.use_ssl,
                plaintext_login=True,
            )
            return connection
        except Exception as exc:
            raise MikroTikError(f"Falha ao conectar na API: {exc}") from exc

    def ensure_user_profile(self):
        pool = self._connect()
        try:
            api = pool.get_api()
            profile_resource = api.get_resource("/ip/hotspot/user/profile")
            existing = profile_resource.get(name=self.cfg.hotspot_profile)
            if existing:
                return

            profile_resource.add(
                name=self.cfg.hotspot_profile,
                **{
                    "session-timeout": "1h",
                    "idle-timeout": "5m",
                    "shared-users": "1",
                    "status-autorefresh": "1m",
                },
            )
        except Exception as exc:
            raise MikroTikError(f"Erro ao criar perfil de hotspot: {exc}") from exc
        finally:
            pool.disconnect()

    def create_hotspot_user(self, username: str, password: str):
        pool = self._connect()
        try:
            api = pool.get_api()
            user_resource = api.get_resource("/ip/hotspot/user")

            existing = user_resource.get(name=username)
            if existing:
                return

            user_resource.add(
                server=self.cfg.hotspot_server,
                name=username,
                password=password,
                profile=self.cfg.hotspot_profile,
                **{"limit-uptime": "1h"},
            )
        except Exception as exc:
            raise MikroTikError(f"Erro ao criar usuário de hotspot: {exc}") from exc
        finally:
            pool.disconnect()
