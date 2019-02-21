import tempfile
import shutil
import os
import subprocess
import urllib.request as urllib2
import re


def getLocalPacages(requirments_folder):
    requirments_folder = requirments_folder.split('/')
    pool_folder = "/"
    for foloder in requirments_folder[0:len(requirments_folder)-1]:
        pool_folder = os.path.join(pool_folder, foloder)
    local_packages = [package.lower()
                      for package in os.listdir(pool_folder)
                      if package not in ['mirror', 'packages.json',
                                         'pypi.json']]
    return local_packages


def setup(tempFolder=None):
    if tempFolder is None:
        tempFolder = tempfile.mkdtemp()
    else:
        if not os.path.exists(tempFolder):
            os.mkdir(tempFolder)
    return tempFolder


def cleanUp(tempFolder):
    shutil.rmtree(tempFolder)


def resolveDependecies(package, templFolder):
    print("Processing deps for %s" % package)
    with open("%s/requirments.in" % templFolder, 'w') as f:
        f.write(package)
    command = 'pip-compile ' \
              '--extra-index-url https://cern.ch/lhcb-pypi/simple/ ' \
              '--trusted-host cern.ch %s/requirments.in' % templFolder
    command = command.split()
    p = subprocess.Popen(command, stdout=subprocess.PIPE)
    out = p.communicate()[0]
    res = []
    for line in out.split(b'\n'):
        if line.startswith(b'--') or line.startswith(b'#'):
            continue
        if not len(line):
            continue
        pkg = line.split(b'==')[0]
        res.append(pkg)
    return res


def getPackageName(package):
    package = package.split('-')
    return {
        'name': package[0],
        'version': package[1]
    }


def organizeDependecies(tempFolder, local_packages, deps):
    print("Moving to folders...")
    for package in deps:
        if os.path.isdir(os.path.join(tempFolder, package)):
            continue
        name = package.lower()
        if name in local_packages:
            continue
        package_folder = os.path.join(tempFolder, name)
        if not os.path.exists(package_folder):
            os.mkdir(package_folder)


def getPackageNameFromUrl(url):
    name = url.split("/")[-1]
    if '#' in name:
        name = name.split('#')[0]
    return name


def downlaodFile(url, name, package_folder, eos_path=None):
    try:
        dest_name = os.path.join(package_folder, name)
        if eos_path:
            eos_des = os.path.join(eos_path, name)
        else:
            eos_des = None
        if os.path.exists(dest_name):
            print("File %s already exists. Skipping..." % dest_name)
            return
        if eos_des and os.path.exists(eos_des):
            print("File %s already exists on EOS. Skipping..." % dest_name)
            return
        print("Downloading %s to %s" % (url, dest_name))
        response = urllib2.urlopen(url)
        data = response.read()
        with open(dest_name, 'wb') as f:
            f.write(data)
    except Exception as e:
        print(e)


def downloadAllPlatforms(tempFolder, eosFolder=None):
    for package in os.listdir(tempFolder):
        if not os.path.isdir(os.path.join(tempFolder, package)):
            continue
        print("Getting all versions for %s" % package)
        try:
            url = 'https://pypi.org/simple/%s/' % package
            response = urllib2.urlopen(url)
            html = response.read().decode('utf-8')
            urls = re.findall(r'href=[\'"]?([^\'" >]+)', html)
            for url in urls:
                name = getPackageNameFromUrl(url)
                if eosFolder:
                    eos_path = os.path.join(eosFolder, package)
                else:
                    eos_path = None
                downlaodFile(url, name, os.path.join(tempFolder, package),
                             eos_path=eos_path)
        except:
            shutil.rmtree(os.path.join(tempFolder, package))
            continue


def moveToEos(tempFolder, eos_path):
    for package in os.listdir(tempFolder):
        if not os.path.isdir(os.path.join(tempFolder, package)):
            continue
        eos_dest = os.path.join(eos_path, package)
        if not os.path.exists(eos_dest):
            os.mkdir(eos_dest)
        for version in os.listdir(os.path.join(tempFolder, package)):
            eos_version_dest = os.path.join(eos_dest, version)
            if not os.path.exists(eos_version_dest):
                shutil.copy2(os.path.join(tempFolder, package, version),
                             eos_version_dest)


def main():
    tempFolder = setup()
    eos_path = '/eos/project/l/lhcbwebsites/www/lhcb-pypi/pool/mirror'
    local_packages = set(getLocalPacages(eos_path))
    all_deps = set()
    for package in local_packages:
        deps = resolveDependecies(package, tempFolder)
        for dep in deps:
            all_deps.add(dep.decode())
    organizeDependecies(tempFolder, local_packages, all_deps)
    downloadAllPlatforms(tempFolder, eos_path)
    moveToEos(tempFolder, eos_path)
    cleanUp(tempFolder)


if __name__ == '__main__':
    main()
