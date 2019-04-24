import logging

# swallow log output
logging.getLogger('klempner').addHandler(logging.NullHandler())
