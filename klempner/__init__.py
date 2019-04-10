from klempner.url import build_url

version_info = (0, 0, 0)
version = '.'.join(str(c) for c in version_info)

__all__ = ['build_url', 'version', 'version_info']
