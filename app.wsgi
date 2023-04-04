import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)) + '/app'
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from app import init_app
application = init_app()

if __name__ == '__main__':
  application.run()
