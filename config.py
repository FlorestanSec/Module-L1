#Config

'''
Modules des variables de configuration de l'application
'''

PARAMETRES_LOGGING =\
{
    'version': 1,
    'formatters': 
    {
        'INFO':
        {
            'format': '[%(levelname)s] × %(message)s',
        },
        'DEBUG':
        {
            'format': '[%(levelname)s] × %(funcName)s × %(lineno)d × %(message)s',
        },
    },
    'handlers':
    {
        'terminal_debug':
        {
            'level': 'DEBUG',
            'formatter': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'fichier_debug':
        {
            'level': 'DEBUG',
            'formatter': 'DEBUG',
            'filename': '[FICHIER]',
            'mode': 'a',
            'class': 'logging.FileHandler',
        },
        'terminal_info':
        {
            'level': 'INFO',
            'formatter': 'INFO',
            'class': 'logging.StreamHandler',
        },
        'fichier_info':
        {
            'level': 'INFO',
            'formatter': 'INFO',
            'filename': '[FICHIER]',
            'mode': 'a',
            'class': 'logging.FileHandler',
        },
    },
    'loggers':
    {
        'fichier':
        {
            
        },
        'fichier.info':
        {
            'level': 'INFO',
            'handlers': ['fichier_info',],
            'propagate': True,
        },
        'fichier.debug':
        {
            'level': 'DEBUG',
            'handlers': ['fichier_debug',],
        },
        'terminal':
        {
        },
        'terminal.info':
        {
            'level': 'INFO',
            'handlers': ['fichier_info', 'terminal_info',],
            'propagate': False,
        },
        'terminal.debug':
        {
            'level': 'DEBUG',
            'handlers': ['fichier_debug', 'terminal_debug',],
        }
    }
}

