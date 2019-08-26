import subprocess

import yaml
import shlex

import os


def env_init():
    env_file = '.env.yaml'
    if os.path.exists(env_file):
        print('find local env file')
        with open(env_file, 'r') as f:
            data = yaml.safe_load(f)
            return data


def main():
    data = env_init()
    vars = ' '.join(
        [str(k) + '=' + shlex.quote(str(v)) for k, v in data.items()
         if k != 'BD_BOT_SERVICE_ACCOUNT_CREDENTIALS'])
    command = 'heroku config:set ' + vars
    # command = 'heroku'
    print(command)

    if True:
        r = subprocess.check_output(shlex.split(command))
        print(r)


if __name__ == '__main__':
    main()
