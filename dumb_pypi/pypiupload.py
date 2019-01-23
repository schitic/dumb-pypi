import os
import json
import subprocess


def auth_pypi():
    credentials_file ='/eos/project/l/lhcbwebsites/www/lhcb-pypi.txt'
    username = None
    password = None
    try:
        with open(credentials_file, 'r') as f:
            tmp = f.read().split('\n')[0:2]
            username, password = tmp
    except Exception as e:
        pass
    return (username, password)


def uploadPackage(package_file):
    username, password = auth_pypi()
    if username and password:
        command = 'twine upload -u %s -p %s %s' % (username, password,
                                                   package_file)
        command = command.split()
        p = subprocess.Popen(command, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        print(stdout)
        if stderr:
            print(stderr)
            return False
        return True
    else:
        return False


def main():
    pool_folder = '/eos/project/l/lhcbwebsites/www/lhcb-pypi/pool/'
    parsed_archives = []
    try:
        with open(os.path.join(pool_folder, 'pypi.json'), 'r') as f:
            parsed_archives = [a.replace('\n', '')
                               for a in json.loads(f.read())]
    except:
        pass

    local_packages = [package
                      for package in os.listdir(pool_folder)
                      if package not in ['mirror', 'packages.json',
                                         'pypi.json']]
    for package in local_packages:
        package_path = os.path.join(pool_folder, package)
        files = [f
                 for f in os.listdir(package_path)
                 if f and f.endswith(('tar.gz', 'tar.bz2', 'whl'))]
        for f in files:
            if f not in parsed_archives:
                if uploadPackage(os.path.join(package_path, f)):
                    parsed_archives.append(f)
    with open(os.path.join(pool_folder, 'pypi.json'), 'w') as f:
        f.write(json.dumps(parsed_archives))


if __name__ == '__main__':
    main()
