import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

import warnings
warnings.filterwarnings('ignore', category=UserWarning, message='TypedStorage is deprecated')

from app import app


if __name__=='__main__':
    app.run('localhost', "3000", debug=True)

    # app.run('192.168.26.75', "5005", debug=True)
    # => http://213.155.192.79:3005/

    


