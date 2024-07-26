import sys
import logging
import logging.config

log = logging.getLogger('')

def parse_cloud_logs(outfile):
   """
      Parses the logs saved in ./output.log from /var/log/cloud-init-output.log
      :param outfile: path to save the parsed logs to
      :returns: None
   """
   try:
      with open('./output.log', 'r') as fh:
         with open(outfile, 'w') as new_fh:
            for line in fh:
               #add parsing here if needed
               new_fh.write(line)
   except Exception as e:
      log.critical(f'Error parsing output logs:\n{e}')

def setup_logging():
   """Sets up the logging configuration for the logger"""
   CONFIG = {
      'version': 1,
      'formatters': {
         # Modify log message format here or replace with your custom formatter class
         'my_formatter': {
            'format': '[%(asctime)s] %(levelname)s pid:%(process)d [%(filename)s.%(funcName)s:%(lineno)d] | %(message)s',
            'datefmt': '%a, %d %b %Y %H:%M:%S'
         }
      },
      'handlers': {
         'console_stderr': {
            # Sends log messages with log level ERROR or higher to stderr
            'class': 'logging.StreamHandler',
            'level': 'ERROR',
            'formatter': 'my_formatter',
            'stream': sys.stderr
         },
         'console_stdout': {
            # Sends log messages with log level lower than ERROR to stdout
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'my_formatter',
            'stream': sys.stdout
         },
      },
      'root': {
         # In general, this should be kept at 'NOTSET'.
         # Otherwise it would interfere with the log levels set for each handler.
         'level': 'NOTSET',
         'handlers': ['console_stderr', 'console_stdout']
      },
   }

   logging.config.dictConfig(CONFIG)

def get_logger(name=""):
   return logging.getLogger(name)
